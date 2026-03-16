import streamlit as st
from compareprice import compare_prices
from database import init_db, get_price_history

st.set_page_config(page_title="ParaTrack", page_icon="💊", layout="wide")

init_db()

st.title("💊 ParaTrack")
st.caption("Comparateur de prix parapharmacie Tunisie — Parafendri vs PharmaShop")

product_name = st.text_input("🔍 Rechercher un produit", placeholder="ex: nivea, avene spf50...")

if product_name:
    with st.spinner("Recherche en cours..."):
        matched_products = compare_prices(product_name)

    if matched_products:
        st.success(f"{len(matched_products)} produit(s) trouvé(s)")

        for product in matched_products:
            with st.container():
                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🟦 Parafendri")
                    if product['image_siteA'] and product['image_siteA'] != "No Image Found":
                        st.image(product['image_siteA'], width=150)
                    st.write(f"**{product['titleA']}**")
                    st.write(f"💰 Prix : `{product['price_siteA']}`")
                    if product['old_price_siteA']:
                        st.write(f"~~{product['old_price_siteA']}~~")
                    st.write(f"📦 Stock : {product['stock_siteA']}")
                    st.markdown(f"[Voir le produit]({product['link_siteA']})")

                    history_a = get_price_history(product['titleA'], 'Parafendri')
                    if len(history_a) > 1:
                        with st.expander("📈 Historique des prix"):
                            dates = [h['scraped_at'] for h in history_a]
                            prices = []
                            for h in history_a:
                                try:
                                    prices.append(float(h['price'].replace('DT', '').replace(',', '.').strip()))
                                except:
                                    prices.append(None)
                            st.line_chart(dict(zip(dates, prices)))

                with col2:
                    st.subheader("🟩 PharmaShop")
                    if product['image_siteB'] and product['image_siteB'] != "No Image Found":
                        st.image(product['image_siteB'], width=150)
                    st.write(f"**{product['titleB']}**")
                    st.write(f"💰 Prix : `{product['price_siteB']}`")
                    if product['old_price_siteB']:
                        st.write(f"~~{product['old_price_siteB']}~~")
                    st.write(f"📦 Stock : {product['stock_siteB']}")
                    st.markdown(f"[Voir le produit]({product['link_siteB']})")

                    history_b = get_price_history(product['titleB'], 'pharmashop')
                    if len(history_b) > 1:
                        with st.expander("📈 Historique des prix"):
                            dates = [h['scraped_at'] for h in history_b]
                            prices = []
                            for h in history_b:
                                try:
                                    prices.append(float(h['price'].replace('DT', '').replace(',', '.').strip()))
                                except:
                                    prices.append(None)
                            st.line_chart(dict(zip(dates, prices)))

                st.caption(f"🎯 Score de similarité : {product['similarity']}%")
    else:
        st.warning("Aucun produit trouvé. Essaie un autre nom.")