import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

BASE_URL = "https://www.parashop.tn"

def scrape_parashop(product_name):
    query   = quote(product_name)
    url     = f"{BASE_URL}/index.php?route=product/search&search={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    products = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup     = BeautifulSoup(response.text, 'html.parser')

        for product in soup.find_all('div', class_='product-thumb'):
            title_tag = product.find('h4', class_='title')
            if title_tag:
                link_tag = title_tag.find('a')
                title    = link_tag.get_text(strip=True) if link_tag else None
                # urljoin gère les liens relatifs et absolus
                link     = urljoin(BASE_URL, link_tag.get('href', '')) if link_tag else ""
            else:
                title = None
                link  = ""

            price_tag = (
                product.find('span', class_='price-new') or
                product.find('p',    class_='price') or
                product.find('span', class_='price-old')
            )
            price = price_tag.get_text(strip=True) if price_tag else None

            img_tag = product.find('img')
            image   = urljoin(BASE_URL, img_tag.get('src', '')) if img_tag else ""

            if title and price:
                products.append({
                    "title":     title,
                    "price":     price,
                    "source":    "Parashop",
                    "link":      link,
                    "image_url": image,
                    "stock":     "available"
                })

        print(f"✅ Parashop: {len(products)} produits")
        return products

    except Exception as e:
        print(f"❌ Parashop erreur: {e}")
        return []