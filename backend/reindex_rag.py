# backend/reindex_rag.py
"""
Script standalone appelé par le cron GitHub Actions
après chaque scraping pour maintenir ChromaDB à jour.
"""
from rag_chatbot import reindex_products

if __name__ == "__main__":
    reindex_products()