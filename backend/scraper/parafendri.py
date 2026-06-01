import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

BASE_URL = "https://parafendri.tn"

def scrape_parafendri(product_name):
    query = quote(product_name)
    url   = f"{BASE_URL}/recherche?search_category=all&controller=search&orderby=position&orderway=desc&s={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    products = []

    while url:
        response = requests.get(url, headers=headers, timeout=10)
        soup     = BeautifulSoup(response.text, 'html.parser')

        for product in soup.find_all('article', class_='product-miniature'):
            stock = "available"
            if product.find('li', class_='out_of_stock'):
                stock = "out of stock"
            elif product.find('div', class_='in-stock'):
                stock = "in stock"

            title_tag = product.select_one('h2.product-title a')
            if title_tag:
                # urljoin garantit un lien absolu même si href est relatif
                link  = urljoin(BASE_URL, title_tag.get('href', ''))
                title = title_tag.get_text(strip=True)
            else:
                link  = ""
                title = None

            price_tag     = product.select_one('.price')
            price         = price_tag.get_text(strip=True) if price_tag else "Price not available"
            old_price_tag = product.select_one('.regular-price')
            old_price     = old_price_tag.get_text(strip=True) if old_price_tag else ""

            img_tag   = product.find('img')
            image_url = urljoin(BASE_URL, img_tag.get('data-src') or img_tag.get('src') or "") if img_tag else ""

            if title:
                products.append({
                    "title":     title,
                    "price":     price,
                    "old_price": old_price,
                    "stock":     stock,
                    "link":      link,
                    "image_url": image_url,
                    "source":    "Parafendri"
                })

        next_btn = soup.select_one('a.next.js-search-link')
        url = next_btn['href'] if next_btn and next_btn.get('href') else None

    return products