import streamlit as st
from compareprice import compare_prices

def app():
    st.title("Product Price Comparison")
    product_name = st.text_input("Enter the product name:")

    if product_name:
        matched_products = compare_prices(product_name)

        if matched_products:
            st.write("Compared products:")
            for product in matched_products:
                st.subheader(product['titleA'])
                st.write(f"Price on Parafendri: {product['price_siteA']}")
                st.write(f"Link to Parafendri: [View product]({product['link_siteA']})")
                st.write(f"Price on PharmaShop: {product['price_siteB']}")
                st.write(f"Link to PharmaShop: [View product]({product['link_siteB']})")
                st.write(f"Similarity: {product['similarity']}%")
        else:
            st.write("No matching products found.")

if __name__ == "__main__":
    app()
