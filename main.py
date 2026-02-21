"""
DarkWeb Monitor - Main Entry Point
Coordinates scraping, parsing, and storing data from dark web sites
"""

import sys
from app.tor_proxy import create_tor_session, test_tor_connection
from app.scraper import scrape_multiple_urls
from app.parser import parse_html
from app.database import DatabaseManager
from app.utils import logger, sanitize_url


def main():
    """Main execution function"""

    logger.info("=" * 60)
    logger.info("🚀 DarkWeb Monitor Starting")
    logger.info("=" * 60)

    # -----------------------------
    # Setup Tor Session
    # -----------------------------
    logger.info("Setting up Tor connection...")
    session = create_tor_session()

    if not test_tor_connection(session):
        logger.error("❌ Failed to establish Tor connection. Ensure Tor is running.")
        sys.exit(1)

    logger.info("✅ Tor connection established successfully")

    # -----------------------------
    # Initialize Database
    # -----------------------------
    logger.info("Connecting to database...")
    db_manager = DatabaseManager()

    if db_manager.collection is None:
        logger.error("❌ Database connection failed. Exiting application.")
        session.close()
        sys.exit(1)

    logger.info("✅ Database connection successful")

    # -----------------------------
    # URLs to Scrape
    # -----------------------------
    urls_to_scrape = [
    "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/",
    "http://awazone7gyw54yau4vb6gvcac4yhnhcf3dkl3cpfxkywqstrgyroliid.onion/auth/register_now"
    ]

    if not urls_to_scrape:
        logger.warning("⚠ No URLs configured for scraping.")
        logger.info("Please add URLs to the urls_to_scrape list in main.py")
        session.close()
        db_manager.close()
        return

    # Sanitize URLs
    valid_urls = []
    for raw_url in urls_to_scrape:
        clean_url = sanitize_url(raw_url)
        if clean_url:
            valid_urls.append(clean_url)

    if not valid_urls:
        logger.error("❌ No valid URLs to scrape after sanitization.")
        session.close()
        db_manager.close()
        return

    # -----------------------------
    # Scrape URLs
    # -----------------------------
    logger.info(f"Starting to scrape {len(valid_urls)} URLs...")
    scraped_results = scrape_multiple_urls(session, valid_urls)

    # -----------------------------
    # Parse and Store Results
    # -----------------------------
    for url, html_content in scraped_results.items():

        if not html_content:
            logger.warning(f"⚠ No content retrieved from {url}")
            continue

        logger.info(f"Parsing content from {url}")
        parsed_data = parse_html(html_content, base_url=url)

        if parsed_data:
            success = db_manager.insert_scraped_data(url, parsed_data)

            if success:
                logger.info(f"✅ Successfully processed and stored data from {url}")
            else:
                logger.error(f"❌ Failed to store data for {url}")
        else:
            logger.warning(f"⚠ Parsing failed for {url}")

    # -----------------------------
    # Retrieve Recent Entries
    # -----------------------------
    logger.info("Retrieving recent entries from database...")
    recent_entries = db_manager.get_recent_entries(limit=5)

    logger.info(f"Found {len(recent_entries)} recent entries")

    # -----------------------------
    # Cleanup
    # -----------------------------
    session.close()
    db_manager.close()

    logger.info("=" * 60)
    logger.info("✅ DarkWeb Monitor Completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logger.info("\n🛑 Operation cancelled by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)