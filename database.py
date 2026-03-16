import sqlite3
from datetime import datetime

DB_PATH = "prices.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT NOT NULL,          -- 'parafendri' or 'pharmashop'
            link TEXT,
            image_url TEXT,
            UNIQUE(title, source)          -- no duplicates
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price TEXT NOT NULL,
            old_price TEXT,
            stock TEXT,
            scraped_at TIMESTAMP NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


def save_product(title, source, link, image_url, price, old_price, stock):
    """Insert or update a product and save its price snapshot"""
    conn = get_connection()
    cursor = conn.cursor()

    # Insert product if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO products (title, source, link, image_url)
        VALUES (?, ?, ?, ?)
    """, (title, source, link, image_url))

    # Get product id
    cursor.execute("""
        SELECT id FROM products WHERE title = ? AND source = ?
    """, (title, source))
    product_id = cursor.fetchone()[0]

    # Save price snapshot
    cursor.execute("""
        INSERT INTO price_history (product_id, price, old_price, stock, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, price, old_price, stock, datetime.utcnow()))

    conn.commit()
    conn.close()


def search_products(query):
    """Return latest price for each product matching the query (both sites)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.title,
            p.source,
            p.link,
            p.image_url,
            ph.price,
            ph.old_price,
            ph.stock,
            ph.scraped_at
        FROM products p
        JOIN price_history ph ON ph.product_id = p.id
        WHERE ph.id = (
            SELECT id FROM price_history
            WHERE product_id = p.id
            ORDER BY scraped_at DESC
            LIMIT 1
        )
        AND LOWER(p.title) LIKE ?
    """, (f"%{query.lower()}%",))

    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        products.append({
            "title": row[0],
            "source": row[1],
            "link": row[2],
            "image_url": row[3],
            "price": row[4],
            "old_price": row[5],
            "stock": row[6],
            "scraped_at": row[7]
        })

    return products


def get_tracked_products():
    """Return all unique products already saved — used by cron job to know what to re-scrape"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT title, source, link FROM products")
    rows = cursor.fetchall()
    conn.close()

    return [{"title": row[0], "source": row[1], "link": row[2]} for row in rows]


def get_price_history(title, source):
    """Return full price history for a specific product"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ph.price, ph.scraped_at
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        WHERE p.title = ? AND p.source = ?
        ORDER BY ph.scraped_at ASC
    """, (title, source))

    rows = cursor.fetchall()
    conn.close()

    return [{"price": row[0], "scraped_at": row[1]} for row in rows]