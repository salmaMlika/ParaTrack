import requests
from bs4 import BeautifulSoup
import csv

product_name = input("Enter the product name to search: ")
url = f"https://pharma-shop.tn/jolisearch?poscats=0&s={product_name}&spr-search-button="

products = []

while url:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    for product in soup.find_all('article', class_='product-miniature js-product-miniature'):
        # Stock
        stock = "available"
        product_out_of_stock = product.find('li', class_='product-flag out_of_stock')
        if product_out_of_stock:
            stock = "out of stock"

        # Title and link
        title_tag = product.find('h2', class_='h3 product-title').find('a')
        title = title_tag.get_text(strip=True)
        link = title_tag.get('href')

        # Price
        price_container = product.find('div', class_='product-price-and-shipping')
        price = price_container.find('span', class_='price')
        old_price = price_container.find('span', class_='regular-price')

        price = price.get_text(strip=True) if price else "Price not available"
        old_price = old_price.get_text(strip=True) if old_price else None

        #image
               
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

    # Verify pagination
    next_button = soup.find('a', class_='next js-search-link')
    if next_button and 'href' in next_button.attrs:
        url = next_button['href']
    else:
        break

# save in csv file
file_path = "data/pharmashop_products.csv"
with open(file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['title', 'link', 'price', 'old_price', 'stock', 'image_url', 'source'])
    writer.writeheader()
    for produit in products:
        writer.writerow(produit)

print(f"Scraping done.there are {len(products)} available products.")
