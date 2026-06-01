import os
import re
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Crée les tables si elles n'existent pas — idempotent"""
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id         SERIAL PRIMARY KEY,
            title      TEXT NOT NULL,
            source     TEXT NOT NULL,
            link       TEXT,
            image_url  TEXT,
            UNIQUE(title, source)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id         SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            price      TEXT NOT NULL,
            old_price  TEXT,
            stock      TEXT,
            scraped_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id         SERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            query      TEXT NOT NULL,
            searched_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # Table abonnements alertes prix
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id         SERIAL PRIMARY KEY,
            email      TEXT NOT NULL,
            product_id INTEGER NOT NULL REFERENCES products(id),
            threshold  FLOAT NOT NULL DEFAULT 5.0,  -- % de baisse minimum pour alerter
            active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE(email, product_id)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# ──────────────────────────────────────────────────────────────
# Recherches
# ──────────────────────────────────────────────────────────────

def save_search(session_id: str, query: str):
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip().lower()
    if not clean:
        return
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO search_history (session_id, query) VALUES (%s, %s)",
        (session_id, clean)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_search_history():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT session_id, query FROM search_history")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"session_id": r[0], "query": r[1]} for r in rows]


# ──────────────────────────────────────────────────────────────
# Produits
# ──────────────────────────────────────────────────────────────

def save_product(title, source, link, image_url, price, old_price, stock):
    conn = get_connection()
    cur  = conn.cursor()

    # Upsert produit
    cur.execute("""
        INSERT INTO products (title, source, link, image_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (title, source) DO UPDATE SET link = EXCLUDED.link, image_url = EXCLUDED.image_url
        RETURNING id
    """, (title, source, link, image_url))

    product_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO price_history (product_id, price, old_price, stock)
        VALUES (%s, %s, %s, %s)
    """, (product_id, price, old_price, stock))

    conn.commit()
    cur.close()
    conn.close()
    return product_id


def search_products(query: str):
    """Retourne le dernier prix connu pour chaque produit matchant la query"""
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT DISTINCT ON (p.id)
            p.id, p.title, p.source, p.link, p.image_url,
            ph.price, ph.old_price, ph.stock, ph.scraped_at
        FROM products p
        JOIN price_history ph ON ph.product_id = p.id
        WHERE LOWER(p.title) LIKE %s
        ORDER BY p.id, ph.scraped_at DESC
    """, (f"%{query.lower()}%",))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{
        "id":         r[0],
        "title":      r[1],
        "source":     r[2],
        "link":       r[3],
        "image_url":  r[4],
        "price":      r[5],
        "old_price":  r[6],
        "stock":      r[7],
        "scraped_at": str(r[8]),
    } for r in rows]


def get_tracked_products():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, title, source, link FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "source": r[2], "link": r[3]} for r in rows]


def get_price_history(title: str, source: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT ph.price, ph.scraped_at
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        WHERE p.title = %s AND p.source = %s
        ORDER BY ph.scraped_at ASC
    """, (title, source))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"price": r[0], "scraped_at": str(r[1])} for r in rows]


# ──────────────────────────────────────────────────────────────
# Alertes prix
# ──────────────────────────────────────────────────────────────

def subscribe_alert(email: str, product_id: int, threshold: float = 5.0):
    """Abonne un email à une alerte de baisse de prix pour un produit"""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO price_alerts (email, product_id, threshold)
        VALUES (%s, %s, %s)
        ON CONFLICT (email, product_id) DO UPDATE SET active = TRUE, threshold = EXCLUDED.threshold
    """, (email, product_id, threshold))
    conn.commit()
    cur.close()
    conn.close()


def get_active_alerts():
    """Retourne tous les abonnements actifs avec le dernier prix connu"""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (pa.id)
            pa.id, pa.email, pa.product_id, pa.threshold,
            p.title, p.source,
            ph.price AS last_price,
            ph.scraped_at
        FROM price_alerts pa
        JOIN products p ON p.id = pa.product_id
        JOIN price_history ph ON ph.product_id = pa.product_id
        WHERE pa.active = TRUE
        ORDER BY pa.id, ph.scraped_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        "alert_id":   r[0],
        "email":      r[1],
        "product_id": r[2],
        "threshold":  r[3],
        "title":      r[4],
        "source":     r[5],
        "last_price": r[6],
        "scraped_at": str(r[7]),
    } for r in rows]


def get_previous_price(product_id: int):
    """Retourne l'avant-dernier prix — pour comparer avec le nouveau"""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT price, scraped_at
        FROM price_history
        WHERE product_id = %s
        ORDER BY scraped_at DESC
        LIMIT 2
    """, (product_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # rows[0] = dernier, rows[1] = avant-dernier
    return rows[1] if len(rows) >= 2 else None