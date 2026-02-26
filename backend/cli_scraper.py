"""
DarkWeb Monitor - FastAPI Main Entry Point
Backend API server using FastAPI
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    health_router,
    scan_router,
    monitors_router,
    alerts_router,
    history_router,
)


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
    # Mix of regular URLs (no Tor) and .onion URLs (Tor required)
    urls_to_scrape = [
        # Regular HTTPS URLs (accessed directly, no Tor proxy)
        "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/",                    # Test HTML page
        "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/",          # Raw text content
        
        # Dark Web .onion URLs (automatically routed through Tor)
        # Note: Requires Tor service running (sudo service tor start)
        # "http://thehiddenwikitorfozq.onion/",       # Hidden Wiki
        # "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/",  # DuckDuckGo onion
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

    # Status summary for final report
    status_summary = {"ONLINE": 0, "OFFLINE": 0, "TIMEOUT": 0, "ERROR": 0}

    # -----------------------------
    # Parse and Store Results
    # -----------------------------
    for url, (html_content, status_info) in scraped_results.items():
        
        url_status = status_info.get("status", "UNKNOWN")
        response_time = status_info.get("response_time", None)
        status_code = status_info.get("status_code", None)
        
        # Log URL status with enhanced logger
        log_url_status(url, url_status, response_time)
        
        # Track status summary
        if url_status in status_summary:
            status_summary[url_status] += 1

        if not html_content:
            logger.warning(f"⚠ No content retrieved from {url} - Status: {url_status}")
            
            # Store status info even if no content (for all statuses including ONLINE)
            db_manager.insert_scraped_data(
                url,
                {
                    "text_content": "",
                    "text_preview": f"Failed to retrieve content - Status: {url_status}",
                    "links": [],
                    "keywords": [],
                    "title": f"[{url_status}] Unable to fetch content",
                    "threat_score": 0,
                    "category": "Unknown",
                    "risk_level": "LOW",
                    "confidence": 0,
                    "emails_found": [],
                    "crypto_addresses": [],
                    "content_hash": ""
                },
                url_status=url_status,
                response_time=response_time,
                status_code=status_code
            )
            continue

        logger.info(f"Parsing content from {url}")
        parsed_data = parse_html(html_content, base_url=url)

        if parsed_data:
            logger.info("Running intelligence analysis...")

            analysis_result = analyze_content(
                        parsed_data["text_content"],
                        parsed_data.get("keywords", [])
                    )

            # Debug: Print analyzer results
            logger.info(f"🔍 Analysis Results: {analysis_result}")

            # Merge analysis into parsed data
            parsed_data.update(analysis_result)

            # =====================================
            # File Download and Analysis Pipeline
            # =====================================
            file_links = parsed_data.get("file_links", [])
            file_analysis_results = []

            if file_links:
                logger.info(f"📥 Found {len(file_links)} downloadable files")
                
                for file_link in file_links:
                    try:
                        file_url = file_link.get("url")
                        logger.info(f"Processing file: {file_link.get('text', 'Unknown')} ({file_link.get('extension')})")
                        
                        # Download file via Tor session
                        download_result = download_file(session, file_url, base_url=url)
                        
                        if download_result.get("success"):
                            file_path = download_result.get("filepath")
                            logger.info(f"✅ Downloaded: {download_result.get('filename')}")
                            
                            # Analyze downloaded file
                            file_analysis = analyze_file(file_path)
                            file_analysis_results.append({
                                "file_url": file_url,
                                "file_name": download_result.get("filename"),
                                "file_size": download_result.get("file_size"),
                                "file_hash": download_result.get("file_hash"),
                                "content_type": download_result.get("content_type"),
                                "analysis": file_analysis
                            })
                            
                        else:
                            logger.warning(f"⚠️ Failed to download: {download_result.get('error')}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error processing file: {e}")
            
            # Add file analysis results to parsed data
            if file_analysis_results:
                parsed_data["file_analysis"] = file_analysis_results

            success = db_manager.insert_scraped_data(
                url,
                parsed_data,
                url_status=url_status,
                response_time=response_time,
                status_code=status_code
            )

            if success:
                logger.info(f"✅ Successfully processed and stored data from {url}")
                
                # =====================================
                # ALERT ENGINE - Check threat conditions
                # =====================================
                alert_triggered = False
                alert_reason = None
                alert_details = {}
                
                threat_score = parsed_data.get("threat_score", 0)
                category = parsed_data.get("category", "Unknown")
                confidence = parsed_data.get("confidence", 0)
                content_changed = parsed_data.get("content_changed", False)
                clamav_detected = parsed_data.get("clamav_detected", False)
                risk_level = parsed_data.get("risk_level", "UNKNOWN")
                
                # Log threat detection with enhanced logger
                if threat_score > 50:
                    log_threat_detection(url, threat_score, category, risk_level)
                
                # Alert Trigger 1: High Threat Score
                if threat_score > 60:
                    alert_triggered = True
                    alert_reason = f"High Threat Score ({threat_score}/100)"
                    alert_details["threat_reason"] = f"Threat score exceeds threshold: {threat_score}"
                
                # Alert Trigger 2: Malware Detected
                if clamav_detected:
                    alert_triggered = True
                    alert_reason = "🚨 MALWARE DETECTED"
                    alert_details["malware_info"] = parsed_data.get("clamav_details")
                    log_malware_detected(url, parsed_data.get("clamav_details", {}))
                
                # Alert Trigger 3: Content Changed
                if content_changed:
                    alert_triggered = True
                    alert_reason = "Content Change Detected"
                    alert_details["content_change"] = True
                    log_content_change(url)
                if content_changed:
                    alert_triggered = True
                    alert_reason = "Content Change Detected"
                    alert_details["content_change"] = True
                
                # Generate and store alert if triggered
                if alert_triggered:
                    db_manager.insert_alert({
                        "url": url,
                        "reason": alert_reason,
                        "threat_score": threat_score,
                        "category": category,
                        "confidence": confidence,
                        "severity": parsed_data.get("risk_level", "UNKNOWN"),
                        "details": alert_details
                    })
                
                # =====================================
                # IOC CORRELATION - Track indicators
                # =====================================
                emails_found = parsed_data.get("emails_found", [])
                crypto_addresses = parsed_data.get("crypto_addresses", [])
                file_hashes = []
                
                # Extract file hashes from file analysis
                if file_analysis_results:
                    for file_result in file_analysis_results:
                        file_hash = file_result.get("file_hash")
                        if file_hash:
                            file_hashes.append(file_hash)
                
                # Track emails for IOC correlation
                ioc_reuse_detected = False
                for email in emails_found:
                    reuse_info = db_manager.insert_ioc(email, "email", url)
                    if reuse_info and reuse_info.get("exists"):
                        ioc_reuse_detected = True
                        log_ioc_reuse("email", email, reuse_info.get('reuse_count'))
                        
                        # Alert on IOC reuse
                        db_manager.insert_alert({
                            "url": url,
                            "reason": "IOC Reuse Detected - Email",
                            "ioc_value": email,
                            "ioc_type": "email",
                            "reuse_count": reuse_info.get("reuse_count"),
                            "severity": "HIGH",
                            "details": {"previous_urls": reuse_info.get("urls")}
                        })
                
                # Track crypto addresses for IOC correlation
                for crypto_addr in crypto_addresses:
                    reuse_info = db_manager.insert_ioc(crypto_addr, "crypto", url)
                    if reuse_info and reuse_info.get("exists"):
                        ioc_reuse_detected = True
                        log_ioc_reuse("crypto", crypto_addr, reuse_info.get('reuse_count'))
                        
                        # Alert on IOC reuse
                        db_manager.insert_alert({
                            "url": url,
                            "reason": "IOC Reuse Detected - Crypto Address",
                            "ioc_value": crypto_addr,
                            "ioc_type": "crypto",
                            "reuse_count": reuse_info.get("reuse_count"),
                            "severity": "HIGH",
                            "details": {"previous_urls": reuse_info.get("urls")}
                        })
                
                # Track file hashes
                for file_hash in file_hashes:
                    reuse_info = db_manager.insert_ioc(file_hash, "file_hash", url)
                    if reuse_info and reuse_info.get("exists"):
                        ioc_reuse_detected = True
                        log_ioc_reuse("file_hash", file_hash, reuse_info.get('reuse_count'))
                        
                        # Alert on IOC reuse
                        db_manager.insert_alert({
                            "url": url,
                            "reason": "IOC Reuse Detected - File Hash",
                            "ioc_value": file_hash,
                            "ioc_type": "file_hash",
                            "reuse_count": reuse_info.get("reuse_count"),
                            "severity": "MEDIUM",
                            "details": {"previous_urls": reuse_info.get("urls")}
                        })
                
                # Update parsed data with IOC reuse flag
                parsed_data["ioc_reuse_detected"] = ioc_reuse_detected
                
            else:
                logger.error(f"❌ Failed to store data for {url}")
        else:
            logger.warning(f"⚠ Parsing failed for {url}")

    # Display URL Status Summary
    logger.info("=" * 60)
    logger.info("📊 URL Status Summary")
    logger.info("=" * 60)
    logger.info(f"🟢 ONLINE  : {status_summary['ONLINE']}")
    logger.info(f"🔴 OFFLINE : {status_summary['OFFLINE']}")
    logger.info(f"🟡 TIMEOUT : {status_summary['TIMEOUT']}")
    logger.info(f"⚠️  ERROR   : {status_summary['ERROR']}")
    logger.info("=" * 60)

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