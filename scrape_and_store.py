"""
Script run by GitHub Actions cron job.
Re-scrapes all products that users have already searched for
and updates their prices in the DB.
"""

from scraper.parafendri import scrape_parafendri
from scraper.pharmashop import scrape_pharmashop
from database import init_db, save_product, get_tracked_products


def scrape_and_store():
    init_db()

    tracked = get_tracked_products()

    if not tracked:
        print("No products tracked yet — DB is empty. Users need to search first.")
        return

    print(f"Re-scraping {len(tracked)} tracked products...")

    for product in tracked:
        title = product['title']
        source = product['source']

        print(f"  Scraping: {title} ({source})")

        # Use first 3 words of title as search query
        query = ' '.join(title.split()[:3])

        if source == 'Parafendri':
            results = scrape_parafendri(query)
        else:
            results = scrape_pharmashop(query)

        # Find the exact product by title match
        for result in results:
            if result['title'].lower() == title.lower():
                save_product(
                    title=result['title'],
                    source=result['source'],
                    link=result['link'],
                    image_url=result.get('image_url', ''),
                    price=result['price'],
                    old_price=result.get('old_price', ''),
                    stock=result.get('stock', 'available')
                )
                print(f"    Updated: {result['price']}")
                break

    print("Done.")


if __name__ == "__main__":
    scrape_and_store()