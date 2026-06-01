# backend/compareprice.py
from scraper.parafendri import scrape_parafendri
from scraper.pharmashop import scrape_pharmashop
from scraper.parashop import scrape_parashop
from database import init_db, save_product
from rapidfuzz import fuzz, process


def is_relevant(product_title: str, search_query: str) -> bool:
    title = product_title.lower()
    query = search_query.lower()
    for kw in query.split():
        if len(kw) > 3 and kw in title:
            return True
    if fuzz.partial_ratio(title, query) >= 40:
        return True
    return False


def parse_price(price_str: str) -> float:
    try:
        return float(
            price_str
            .replace("DT", "").replace("dt", "")
            .replace("\xa0", "").replace(" ", "")
            .replace(",", ".")
            .strip()
        )
    except Exception:
        return 0.0


def group_products(products: list, similarity_threshold: int = 72) -> list:
    groups = []
    used   = set()
    titles = [p["title"] for p in products]

    for i, product in enumerate(products):
        if i in used:
            continue

        matches = process.extract(
            product["title"],
            titles,
            scorer=fuzz.token_sort_ratio,
            limit=None,
            score_cutoff=similarity_threshold,
        )

        group_list = []
        for _, score, j in matches:
            if j not in used:
                used.add(j)
                group_list.append(products[j])

        if not group_list:
            continue

        canonical = max(group_list, key=lambda p: len(p["title"]))

        offers = []
        for p in group_list:
            price_val = parse_price(p["price"])
            offers.append({
                "source":    p["source"],
                "price":     p["price"],
                "price_val": price_val,
                "link":      p.get("link", ""),
                "image_url": p.get("image_url", ""),
                "stock":     p.get("stock", "available"),
                # id depuis la DB pour les alertes
                "product_id": p.get("product_id", 0),
            })

        offers.sort(key=lambda o: o["price_val"] if o["price_val"] > 0 else 9999)

        prices     = [o["price_val"] for o in offers if o["price_val"] > 0]
        min_price  = min(prices) if prices else 0
        max_price  = max(prices) if prices else 0
        saving_pct = round(((max_price - min_price) / max_price) * 100) if max_price > 0 and len(prices) > 1 else 0

        groups.append({
            "titleA":      canonical["title"],
            # id du produit canonique (moins cher / premier) pour les alertes
            "id":          offers[0].get("product_id", 0),
            "offers":      offers,
            "min_price":   min_price,
            "max_price":   max_price,
            "saving_pct":  saving_pct,
            "image_url":   offers[0].get("image_url", ""),
            "best_source": offers[0]["source"] if offers else "",
        })

    groups.sort(key=lambda g: len(g["offers"]), reverse=True)
    return groups


def compare_prices(product_name: str) -> list:
    init_db()
    print(f"🔍 Recherche: {product_name}")

    all_products = []
    all_products.extend(scrape_parafendri(product_name))
    all_products.extend(scrape_pharmashop(product_name))
    all_products.extend(scrape_parashop(product_name))

    if not all_products:
        return []

    filtered = [p for p in all_products if p.get("title") and is_relevant(p["title"], product_name)]
    print(f"📊 {len(all_products)} → {len(filtered)} pertinents")

    # Sauvegarde et récupère l'id DB pour chaque produit
    for p in filtered:
        try:
            product_id = save_product(
                title=p["title"], source=p["source"],
                link=p.get("link", ""), image_url=p.get("image_url", ""),
                price=p["price"], old_price=p.get("old_price", ""),
                stock=p.get("stock", "available"),
            )
            p["product_id"] = product_id  # injecte l'id dans le dict
        except Exception as e:
            print(f"  ⚠️ {e}")
            p["product_id"] = 0

    grouped = group_products(filtered)
    print(f"📦 {len(filtered)} → {len(grouped)} groupes")
    return grouped