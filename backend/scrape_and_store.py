from scraper.parafendri import scrape_parafendri
from scraper.pharmashop import scrape_pharmashop
from scraper.parashop import scrape_parashop
from database import init_db, save_product, get_tracked_products


SCRAPERS = {
    "Parafendri": scrape_parafendri,
    "pharmashop": scrape_pharmashop,
    "Parashop":   scrape_parashop,
}


def scrape_and_store():
    """
    Re-scrape tous les produits déjà suivis en DB pour mettre à jour
    l'historique des prix (utilisé par Prophet).
    Appelé par le cron job GitHub Actions toutes les 6h.
    """
    init_db()
    tracked = get_tracked_products()

    if not tracked:
        print("📭 Aucun produit suivi en DB — lance d'abord une recherche depuis l'app")
        return

    print(f"🔄 Mise à jour de {len(tracked)} produits...")

    # Regroupe par source pour éviter les requêtes dupliquées
    by_source: dict[str, list[str]] = {}
    for product in tracked:
        source = product["source"]
        title  = product["title"]
        # Utilise les 4 premiers mots comme query de recherche
        query  = " ".join(title.split()[:4])
        by_source.setdefault(source, []).append(query)

    for source, queries in by_source.items():
        scraper = SCRAPERS.get(source)
        if not scraper:
            print(f"⚠️  Pas de scraper pour '{source}' — ignoré")
            continue

        # Déduplique les queries
        unique_queries = list(dict.fromkeys(queries))

        for query in unique_queries:
            print(f"  [{source}] {query}")
            try:
                results = scraper(query)
                saved = 0
                for r in results:
                    save_product(
                        title     = r["title"],
                        source    = r["source"],
                        link      = r.get("link", ""),
                        image_url = r.get("image_url", ""),
                        price     = r["price"],
                        old_price = r.get("old_price", ""),
                        stock     = r.get("stock", "available"),
                    )
                    saved += 1
                print(f"    ✅ {saved} prix enregistrés")
            except Exception as e:
                print(f"    ❌ Erreur: {e}")

    print("✅ Mise à jour terminée")


if __name__ == "__main__":
    scrape_and_store()