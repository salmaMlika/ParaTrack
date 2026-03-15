import re
import unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scraper.parafendri import scrape_parafendri
from scraper.pharmashop import scrape_pharmashop

SIMILARITY_THRESHOLD = 0.40


def preprocess(text):
    # Lowercase, remove accents, keep only alphanumeric
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def compare_prices(product_name):
    parafendri_products = scrape_parafendri(product_name)
    pharmashop_products = scrape_pharmashop(product_name)

    if not parafendri_products or not pharmashop_products:
        return []

    titles_a = [preprocess(p["title"]) for p in parafendri_products]
    titles_b = [preprocess(p["title"]) for p in pharmashop_products]

    # Vectorize all titles together so IDF weights are comparable
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    tfidf_matrix = vectorizer.fit_transform(titles_a + titles_b)

    n = len(titles_a)
    similarity_matrix = cosine_similarity(tfidf_matrix[:n], tfidf_matrix[n:])

    matches = []
    for i, product_a in enumerate(parafendri_products):
        best_idx = np.argmax(similarity_matrix[i])
        best_score = similarity_matrix[i][best_idx]

        if best_score >= SIMILARITY_THRESHOLD:
            best_match = pharmashop_products[best_idx]
            matches.append({
                'titleA': product_a['title'],
                'price_siteA': product_a['price'],
                'old_price_siteA': product_a.get('old_price', ''),
                'link_siteA': product_a['link'],
                'image_siteA': product_a.get('image_url', ''),
                'stock_siteA': product_a.get('stock', 'available'),
                'titleB': best_match['title'],
                'price_siteB': best_match['price'],
                'old_price_siteB': best_match.get('old_price', ''),
                'link_siteB': best_match['link'],
                'image_siteB': best_match.get('image_url', ''),
                'stock_siteB': best_match.get('stock', 'available'),
                'similarity': round(best_score * 100, 1)
            })

    return matches