# 🔧 Scraper Fix - Implementation Complete

## ✅ Issues Fixed

### 1. **Missing Response Headers Bug**
**Problem:** `fetch_url()` wasn't returning `response_headers`, causing content-type validation to fail.  
**Impact:** ALL URLs were rejected as "Non-HTML content" even when they contained valid HTML.  
**Fix:** Added `response_headers` to the return dictionary in `fetch_url()`.

### 2. **Overly Strict Content-Type Checking**
**Problem:** Code only accepted `text/html` or `text/plain` content types.  
**Impact:** Valid pages were rejected if server sent different/missing content-type headers.  
**Fix:** Changed to permissive approach - only reject known binary content types.

```python
# Old (too strict)
if "text/html" not in content_type and "text/plain" not in content_type:
    return None

# New (permissive)
if content_type and not any(t in content_type for t in ["text/", "application/json", "application/xml"]):
    return None
```

### 3. **Regular URLs Through Tor**
**Problem:** ALL URLs (including regular HTTPS) were routed through Tor proxy.  
**Impact:** Sites like pastebin.com blocked Tor exit nodes (403 errors).  
**Fix:** Auto-detect `.onion` URLs and only use Tor proxy for those.

```python
# Now automatically detects .onion URLs
use_tor = ".onion" in url.lower()
proxies = TOR_PROXIES if use_tor else None
```

### 4. **Missing Data Storage for ONLINE Status**
**Problem:** When URL was ONLINE but content failed validation, nothing was stored.  
**Impact:** No database record created, making it hard to track issues.  
**Fix:** Store placeholder data for all failure cases (including ONLINE with no content).

## 🧪 Test Your Fixes

### Test 1: Regular HTTPS URL (without Tor)
```python
urls_to_scrape = [
    "https://pastebin.com/raw/iAjZBHth",  # Now works without Tor blocking
]
```

Run: `python backend/main.py`

**Expected:** Should fetch content successfully without 403 error.

### Test 2: Onion URL (with Tor)
```python
urls_to_scrape = [
    "http://thehiddenwikitorfozq.onion/",  # Hidden Wiki
]
```

**Expected:** Uses Tor proxy automatically, fetches .onion content.

### Test 3: Mixed URLs
```python
urls_to_scrape = [
    "https://pastebin.com/raw/iAjZBHth",              # Regular (no Tor)
    "http://thehiddenwikitorfozq.onion/",             # Onion (Tor)
    "https://www.example.com",                        # Regular (no Tor)
]
```

**Expected:** Automatically routes each URL appropriately.

## 📋 Working Test URLs

### Regular HTTPS URLs (No Tor needed)
```python
"https://pastebin.com/raw/iAjZBHth",           # Raw text paste
"https://example.com",                         # Simple test page
"https://httpbin.org/html",                    # HTML response test
"https://api.github.com/users/octocat",        # JSON API (also accepted)
```

### Onion URLs (Tor required - must have Tor running)
```python
"http://thehiddenwikitorfozq.onion/",                                    # Hidden Wiki
"https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/", # DuckDuckGo
"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/", # Ahmia search
```

**Note:** Onion URLs require Tor service running: `sudo systemctl start tor` or `sudo service tor start`

## 🚦 Verify Logs

### Check System Log
```bash
cat backend/logs/system.log | tail -30
```

**What to look for:**
- ✅ "URL ONLINE" messages with response times
- ✅ Content-type information in logs
- ✅ Proper routing (Tor for .onion, direct for others)
- ❌ No more "Non-HTML content" for valid pages

### Check Alert Log
```bash
cat backend/logs/alerts.log | tail -20
```

**What to look for:**
- ⚠️ Only genuine errors (TIMEOUT, OFFLINE, real errors)
- ⚠️ Threat detections (if found)
- ✅ No false "Non-HTML" warnings

## 🔍 Debugging Tips

### If Pastebin still returns 403:
```bash
# Test direct access (should work now)
curl https://pastebin.com/raw/iAjZBHth

# If it works in curl but not in script, check firewall/VPN
```

### If .onion URLs don't work:
```bash
# Verify Tor is running
sudo systemctl status tor

# Test Tor proxy
curl --socks5-hostname 127.0.0.1:9050 http://thehiddenwikitorfozq.onion/

# Start Tor if needed
sudo systemctl start tor
```

### If content is empty:
Check the logs for:
- "Empty content received from {url}" - means response was blank
- "Non-text content at {url}" - means binary content (image, pdf, etc.)
- Content-Type header value in logs

## 📊 Expected Database Results (After Fix)

### Successful Scrape
```json
{
  "url": "https://pastebin.com/raw/iAjZBHth",
  "url_status": "ONLINE",
  "status_code": 200,
  "text_content": "[actual content here]",
  "text_preview": "[first 500 chars]",
  "links": [...],
  "keywords": [...],
  "threat_score": 15,
  "category": "Document/Info",
  "risk_level": "LOW"
}
```

### Failed Scrape (with proper tracking)
```json
{
  "url": "http://invalid-site.onion/",
  "url_status": "OFFLINE",
  "status_code": null,
  "text_content": "",
  "text_preview": "Failed to retrieve content - Status: OFFLINE",
  "threat_score": 0,
  "category": "Unknown",
  "risk_level": "LOW"
}
```

## 🎯 Next Steps

1. **Update your URLs** in `backend/main.py` with working test URLs
2. **Run the script**: `python backend/main.py`
3. **Check logs**: `cat backend/logs/system.log`
4. **Verify MongoDB**: Check that content is actually being parsed and analyzed
5. **Test both types**: Try regular HTTPS URLs and .onion URLs

## 📝 Code Changes Summary

### Modified Files
- ✅ [backend/app/scraper.py](backend/app/scraper.py)
  - Added `response_headers` to fetch_url return
  - Improved content-type validation (permissive approach)
  - Auto-detect .onion URLs for Tor routing
  - Added empty content check

- ✅ [backend/main.py](backend/main.py)
  - Fixed ONLINE status handling (now stores data even when content fails)
  - Better error tracking for all URL statuses

## 🧪 Quick Test Script

Add this to test the fixes:

```python
# In backend/main.py, replace urls_to_scrape with:
urls_to_scrape = [
    "https://httpbin.org/html",  # Should work - HTML test page
]

# Run and check database - should see actual parsed content now!
```

---

**Status:** ✅ **FIXES APPLIED - Test with working URLs to verify**
