import requests
from bs4 import BeautifulSoup
import csv
import os



#make request
url="https://www.parashop.tn/visage"
response=requests.get(url)
#analyse the  HTML content
soup=BeautifulSoup(response.text,'html.parser')

products =[]
while True:
 for product in soup.find_all('div',class_='product-thumb'):
    #stock
    stock="available"
    product_label= product.find('div',class_='product-labels')
    if product_label:
        out_of_stock=product_label.find('span',class_='product-label product-label-30 product-label-default')
        if out_of_stock:
           stock="out of stock"
        
    #link
    link=product.find('div',class_='name').find('a').get('href')
    #title
    title=product.find('div',class_='name').find('a').get_text()
    #price
    old_price=product.find('div',class_='price').find('span',class_='price-old')  
    new_price=product.find('div',class_='price').find('span',class_='price-new')  
    normal_price=product.find('div',class_='price').find('span',class_='price-normal')

    if old_price and new_price:
        price=new_price.get_text()
        old_price=old_price.get_text()
    elif normal_price:
           price=normal_price.get_text()
    else:
        price = "Price not available"
    #image
    image_url = "No Image Found"

    img_tag = product.find('img', class_='img-responsive')

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
        "source":"parashop"

    })

 file_path="data/parashop_products.csv"
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
 print("jawek behi")


    
