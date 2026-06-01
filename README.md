# ParaTrack : Parapharmacy Product Price Comparison Tool

## Overview

This project is a **Parapharmacy Product Price Comparison Tool**. The application scrapes product data from two  ParaPharmacies (**Parafendri** : https://parafendri.tn/  and **PharmaShop** : https://pharma-shop.tn/) to compare prices of a wide range of products, including **skincare**, **bodycare**, and other **parapharmacy** items, helping users find the best deals available.

I created this project out of **personal interest and fun**, as a way to build something that is both practical and efficient.

## Key Features

- **Web Scraping**: Scrapes product data (title, price, availability) from **Parafendri** and **PharmaShop** using Python’s **BeautifulSoup** and **Requests** libraries.
- **Price Comparison**: Automatically compares the prices of the same product across two platforms.
- **Similarity Matching**: Uses **FuzzyWuzzy** to compare product titles and calculate the similarity percentage to ensure accurate matches.
- **Interactive UI**: Built with **Streamlit**, providing a simple and easy-to-use interface for product comparison.
- **Product Details**: Displays product title, price, links to the product pages, and similarity score.

---

## Technologies Used

- **Python**: Core programming language used for scraping, data processing.
- **Streamlit**: Used for creating the interactive user interface.
- **BeautifulSoup**: Used for parsing and scraping HTML data from the websites.
- **Requests**: For making HTTP requests to fetch the web pages.
- **FuzzyWuzzy**: For fuzzy string matching to compare product titles.
- **Pandas**: For handling and manipulating data.

---

## How It Works

1. **User Input**: The user enters the name of a product they wish to compare.
2. **Web Scraping**: The app scrapes product data from the two platforms.
3. **Comparison**: The app compares the prices of the same product from both sites and displays the results.
4. **Similarity Scoring**: The similarity of the product titles is calculated to ensure accurate matching.
5. **Product Display**: The app shows the product details, including price, product link, and similarity score.

---

## How to Run

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/parapharmacy-product-price-comparison.git
   cd parapharmacy-product-price-comparison

 2.Install the required dependencies:

    pip install -r requirements.txt

3.Run the Streamlit app:

    streamlit run app.py

---
## Future Enhancements

   1. Next.js Migration: I plan to migrate the frontend to Next.js to improve performance, scalability, and user experience.

   2.Machine Learning & Data Science: In the future, I plan to integrate machine learning models to optimize product recommendations based on user data.

