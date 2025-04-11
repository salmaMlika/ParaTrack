from fuzzywuzzy import fuzz
import pandas as pd
from scraper.parafendri import scrape_parafendri
from scraper.pharmashop import scrape_pharmashop

def compare_prices(product_name):
    # Scrape data from both websites
    parafendri_products = scrape_parafendri(product_name)
    pharmashop_products = scrape_pharmashop(product_name)

    matched_products = []

    # Compare the products from both websites
    for product_a in parafendri_products:
        title_a = product_a["title"]
        best_match = None
        best_score = 0

        for product_b in pharmashop_products:
            title_b = product_b["title"]
            # Calculate similarity score
            score = fuzz.token_set_ratio(title_a.lower(), title_b.lower())

            if score > best_score:
                best_score = score
                best_match = product_b

        if best_score >= 90:   
            matched_products.append({
                'titleA': product_a['title'],
                'price_siteA': product_a['price'],
                'link_siteA': product_a['link'],
                'titleB': best_match['title'],
                'price_siteB': best_match['price'],
                'link_siteB': best_match['link'],
                'similarity': best_score
            })
    
    return matched_products
