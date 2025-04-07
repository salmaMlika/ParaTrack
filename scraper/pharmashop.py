import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

#make request
url="https://pharma-shop.tn/839-visage"
response=requests.get(url)
#analyse the  HTML content
soup=BeautifulSoup(response.text,'html.parser')

products =[]
while True:
 for product in soup.find_all('article',class_='product-miniature js-product-miniature'):
    #stock
    stock="available"
    product_out_of_stock= product.find('li',class_='product-flag out_of_stock')
    if product_out_of_stock:
           stock="out of stock"
    #print(stock)
    #link
    link=product.find('h2',class_='h3 product-title').find('a').get('href')
    #title
    title=product.find('h2',class_='h3 product-title').find('a').get_text()
    #price
    old_price=product.find('div',class_='product-price-and-shipping').find('span',class_='regular-price')  
    price=product.find('div',class_='product-price-and-shipping').find('span',class_='price')  

    if old_price:
        old_price=old_price.get_text()
        price=price.get_text()
    elif not old_price:
           price=price.get_text()
    else:
        price = "Price not available"
    #image
    image_url = "No Image Found"

    img_tag = product.find('a', class_='thumbnail product-thumbnail').find('img')

    if img_tag:
     image_url = img_tag.get('data-src') or img_tag.get('src')
    
    else:
        image_url = "No Image Found"
    
    
    products.append({
        "title": title,
        "link": link,
        "price": price,
        "old_price": old_price,
        "stock": stock,
        "image_url": image_url,
        "source":"pharmashop"
    })
 file_path="data/pharmashop_products.csv"
 with open(file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['title', 'link', 'price', 'old_price', 'stock', 'image_url','source'])
    writer.writeheader()
    for produit in products:
        writer.writerow(produit)
 next_button = soup.find('a', class_='next js-search-link')
 if next_button and 'href' in next_button.attrs:
        url = f"{next_button['href']}"
 else:
        url = None
