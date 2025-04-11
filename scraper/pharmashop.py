import requests
from bs4 import BeautifulSoup

def scrape_pharmashop(product_name):
    url = f"https://pharma-shop.tn/jolisearch?poscats=0&s={product_name}&spr-search-button="
    products = []

    while url:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for product in soup.find_all('article', class_='product-miniature js-product-miniature'):
            stock = "available"
            if product.find('li', class_='product-flag out_of_stock'):
                stock = "out of stock"

            title_tag = product.find('h2', class_='h3 product-title').find('a')
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href')

            price_container = product.find('div', class_='product-price-and-shipping')
            price = price_container.find('span', class_='price')
            old_price = price_container.find('span', class_='regular-price')

            price = price.get_text(strip=True) if price else "Price not available"
            old_price = old_price.get_text(strip=True) if old_price else None

            img_tag = product.find('a', class_='thumbnail product-thumbnail').find('img')
            image_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else "No Image Found"

            products.append({
                "title": title,
                "link": link,
                "price": price,
                "old_price": old_price,
                "stock": stock,
                "image_url": image_url,
                "source": "pharmashop"
            })

        next_button = soup.find('a', class_='next js-search-link')
        if next_button and 'href' in next_button.attrs:
            url = next_button['href']
        else:
            break

    return products
