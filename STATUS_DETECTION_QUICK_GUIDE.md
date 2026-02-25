# URL Status Detection - Quick Reference

## What Changed

The monitor now tracks four URL availability states:

| Status | Meaning | Example |
|--------|---------|---------|
| ONLINE | URL responded with HTTP 200 | Site accessible, content scraped |
| OFFLINE | Connection refused | Tor network rejected connection |
| TIMEOUT | Server did not respond in time | Site down or DDos'd |
| ERROR | Other network or HTTP errors | Non-200 status, SSL errors |

## Files Updated

### 1. backend/app/scraper.py
- Adds `fetch_url()` with granular exception handling.
- Returns `{status, content, response_time, status_code}`.
- Uses Tor proxy automatically for .onion URLs.

### 2. backend/app/database.py
- Stores `url_status`, `response_time`, `status_code`.
- Maintains `status_history` over time.

### 3. backend/main.py
- Extracts status from scraper results.
- Writes status into MongoDB.
- Prints a status summary at the end of a run.

## Data Flow (Simplified)

```python
# Before
scrape_url(session, url)  # content only

# After
fetch_url(url)  # status, content, response_time, status_code
```

## MongoDB Storage Example

```json
{
  "url": "http://marketplace.onion",
  "url_status": "ONLINE",
  "response_time": 2.34,
  "status_code": 200,
  "status_history": [
    {
      "timestamp": "2026-02-21T14:30:45Z",
      "url_status": "ONLINE",
      "response_time": 2.34,
      "status_code": 200
    }
  ]
}
```

## Manual Test

```python
from app.scraper import fetch_url

result = fetch_url("http://example.com")
print(result["status"], result["response_time"])
```

## Run the Pipeline

```bash
python backend/main.py
```

## Why It Matters

- You get clear availability signals for each URL.
- Status history supports trend analysis.
- Failures are stored without crashing the pipeline.
