import requests
from bs4 import BeautifulSoup

def scrape_parafendri(product_name):
    base_url = "https://parafendri.tn"
    url = f"{base_url}/recherche?controller=search&s={product_name}"

    products = []

    while url:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for product in soup.find_all('div', class_='item-product product_per_3 col-xs-12 col-sm-6 col-md-6 col-lg-4 col-xl-4'):
            # Stock
            stock = "available"
            product_label = product.find('div', class_='product-flag')
            if product_label and product_label.find('li', class_='out_of_stock'):
                stock = "out of stock"

            # Link & Title
            product_desc = product.find('div', class_='product_desc').find('a')
            link = product_desc.get('href')
            title = product_desc.get_text(strip=True)

            # Price
            price_block = product.find('div', class_='product-price-and-shipping')
            old_price_tag = price_block.find('span', class_='regular-price')
            new_price_tag = price_block.find('span', class_='price price-sale')
            normal_price_tag = price_block.find('span', class_='price')

            old_price = ""
            if old_price_tag and new_price_tag:
                price = new_price_tag.get_text(strip=True)
                old_price = old_price_tag.get_text(strip=True)
            elif normal_price_tag:
                price = normal_price_tag.get_text(strip=True)
            else:
                price = "Price not available"

            # Image
            img_tag = product.find('img')
            image_url = (
                img_tag.get('data-full-size-image-url') or
                img_tag.get('data-src') or
                img_tag.get('src') or
                "No Image Found"
            ) if img_tag else "No Image Found"

            # Append
            products.append({
                "title": title,
                "price": price,
                "old_price": old_price,
                "stock": stock,
                "link": link,
                "image_url": image_url,
                "source": "Parafendri"
            })

        # Pagination
        next_button = soup.find('a', class_='next js-search-link')
        if next_button and 'href' in next_button.attrs:
            url = next_button['href']
        else:
            break

    return products   
