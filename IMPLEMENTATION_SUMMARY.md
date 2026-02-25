# URL Status Detection - Implementation Summary

## What Was Implemented

The monitor now classifies URL availability into four states:

- ONLINE: HTTP 200 response with content
- OFFLINE: Connection refused
- TIMEOUT: Connect or read timeout
- ERROR: Other HTTP or network errors

## Files Modified

### backend/app/scraper.py
- Added `fetch_url()` with granular exception handling.
- Returns `{status, content, response_time, status_code}`.
- Routes .onion URLs through Tor automatically.

### backend/app/database.py
- Stores `url_status`, `response_time`, `status_code`.
- Maintains `status_history` for each URL over time.

### backend/main.py
- Extracts status info from scraper results.
- Writes status metadata even when content is missing.
- Prints a status summary after each run.

## Run the Pipeline

```bash
python backend/main.py
```

## Configuration

- Adjust timeouts in `backend/app/config.py`.
- Update Tor proxy settings in `backend/app/scraper.py` if needed.

## Benefits

- Clear availability signals for each URL.
- Status history for trend analysis.
- Graceful handling of failures without crashing.
