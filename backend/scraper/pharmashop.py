import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

BASE_URL = "https://pharma-shop.tn"

def scrape_pharmashop(product_name):
    url     = f"{BASE_URL}/jolisearch?poscats=0&s={product_name}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup     = BeautifulSoup(response.text, 'html.parser')
        products = []

        for price_elem in soup.find_all('span', class_=re.compile(r'price')):
            # Remonte au parent article
            container = price_elem
            for _ in range(6):
                container = container.parent
                if container and container.name == 'article':
                    break

            if not (container and container.name == 'article'):
                continue

            title_elem = container.find('h2') or container.find('h3')
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            price = price_elem.get_text(strip=True)

            # Cherche le lien dans l'article
            link_tag = container.find('a', href=True)
            link     = urljoin(BASE_URL, link_tag['href']) if link_tag else ""

            # Cherche l'image
            img_tag   = container.find('img')
            image_url = urljoin(BASE_URL, img_tag.get('src', '')) if img_tag else ""

            products.append({
                "title":     title,
                "price":     price,
                "source":    "Pharmashop",
                "link":      link,
                "image_url": image_url,
                "stock":     "available"
            })

        print(f"📦 Pharmashop: {len(products)} produits")
        return products

    except Exception as e:
        print(f"❌ Pharmashop: {e}")
        return []