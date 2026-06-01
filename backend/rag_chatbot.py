# backend/rag_chatbot.py
"""
Vrai RAG (Retrieval Augmented Generation) :
1. Les produits sont indexés dans ChromaDB avec sentence-transformers
2. À chaque message, on embed la query et on retrieve les 5 produits les plus proches
3. Ces produits sont injectés dans le prompt Groq comme contexte réel

Différence avec l'ancien système :
- Ancien : SQL LIKE '%query%' → résultats exacts seulement
- Nouveau : similarité sémantique → "crème hydratante" trouve aussi "soin nourrissant"
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from database import search_products, get_connection
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
client       = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ──────────────────────────────────────────────────────────────
# CHROMADB SETUP
# ──────────────────────────────────────────────────────────────

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

_chroma_client     = None
_chroma_collection = None

def get_chroma_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection

    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # sentence-transformers multilingue — gère français + arabe + anglais
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    _chroma_collection = _chroma_client.get_or_create_collection(
        name="paratrack_products",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return _chroma_collection


# ──────────────────────────────────────────────────────────────
# INDEXATION — appelée par le cron job après chaque scraping
# ──────────────────────────────────────────────────────────────

def reindex_products():
    """
    Charge tous les produits de Supabase et les indexe dans ChromaDB.
    Idempotent — upsert par product_id.
    """
    print("🔄 Réindexation RAG...")

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (p.id)
            p.id, p.title, p.source, p.link,
            ph.price, ph.stock
        FROM products p
        JOIN price_history ph ON ph.product_id = p.id
        ORDER BY p.id, ph.scraped_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("  Aucun produit à indexer")
        return

    collection = get_chroma_collection()

    # Batch upsert par chunks de 100
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]

        ids       = []
        documents = []
        metadatas = []

        for r in batch:
            pid, title, source, link, price, stock = r
            doc_id = str(pid)

            # Document = ce qui sera embedé et searché
            document = f"{title} | {source} | {price}"

            ids.append(doc_id)
            documents.append(document)
            metadatas.append({
                "title":  title,
                "source": source,
                "price":  str(price),
                "link":   str(link or ""),
                "stock":  str(stock or "available"),
            })

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  ✅ {min(i + batch_size, len(rows))}/{len(rows)} produits indexés")

    print(f"✅ RAG: {len(rows)} produits dans ChromaDB")


# ──────────────────────────────────────────────────────────────
# RETRIEVAL — cœur du RAG
# ──────────────────────────────────────────────────────────────

def retrieve_products(query: str, n_results: int = 5) -> list[dict]:
    """
    Embed la query et retrouve les n produits les plus proches
    dans l'espace vectoriel ChromaDB.
    """
    try:
        collection = get_chroma_collection()
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
        )

        products = []
        if results and results["metadatas"]:
            for meta in results["metadatas"][0]:
                products.append(meta)
        return products

    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return []


def format_context(products: list[dict]) -> str:
    if not products:
        return ""
    lines = ["📦 Produits trouvés dans notre catalogue :"]
    for p in products:
        stock_icon = "✅" if p.get("stock") == "available" else "❌"
        lines.append(f"  • {p['title']} — {p['price']} chez {p['source']} {stock_icon}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un assistant expert en parapharmacie en Tunisie pour ParaTrack.

🟢 RÈGLES :
- Réponds TOUJOURS en français, de façon naturelle et utile
- Utilise le contexte produits fourni pour donner des prix réels
- Si plusieurs prix existent pour le même produit, indique le moins cher
- Pour les routines de soins, donne des recommandations concrètes avec des marques
- Ne dis jamais que tu "cherches" ou "appelles une fonction" — réponds directement

🌍 Contexte :
- Prix en DT (dinars tunisiens)
- Sites disponibles : Parafendri, PharmaShop, Parashop
- Marques populaires en Tunisie : SVR, Avène, Bioderma, La Roche-Posay, Nuxe, Vichy, CeraVe

💡 Exemples de bonnes réponses :
- "La crème SVR Topialyse est à 38.500 DT chez Parafendri, contre 42.000 DT chez PharmaShop — meilleur prix chez Parafendri."
- "Pour peau grasse je recommande : nettoyant La Roche-Posay Effaclar (~28 DT), sérum niacinamide SVR (~35 DT), SPF50 Avène (~44 DT)."
"""


# ──────────────────────────────────────────────────────────────
# CHAT PRINCIPAL
# ──────────────────────────────────────────────────────────────

def chat_with_rag(user_message: str) -> str:
    if not client:
        return "⚠️ API Groq non configurée"

    # 1. Retrieval sémantique depuis ChromaDB
    products = retrieve_products(user_message, n_results=6)

    # 2. Fallback SQL si ChromaDB vide (pas encore indexé)
    if not products:
        sql_products = search_products(user_message)
        products = [
            {"title": p["title"], "price": p["price"],
             "source": p["source"], "stock": p.get("stock", "available")}
            for p in sql_products[:6]
        ]

    context = format_context(products)

    # 3. Prompt avec contexte injecté
    prompt = f"""Question de l'utilisateur : {user_message}

{context if context else "Aucun produit trouvé dans le catalogue pour cette recherche."}

Réponds de façon utile et naturelle en utilisant ces informations."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"[Groq ERROR] {e}")
        return f"Erreur: {str(e)}"


if __name__ == "__main__":
    # Test — indexe d'abord puis chat
    reindex_products()
    print("\n🤖 Chatbot RAG — tape 'quit' pour quitter\n")
    while True:
        msg = input("🧑 Vous: ")
        if msg.lower() == "quit":
            break
        print(f"🤖 Bot: {chat_with_rag(msg)}\n")