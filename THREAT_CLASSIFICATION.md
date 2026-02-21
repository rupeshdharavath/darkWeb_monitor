# Advanced Threat Classification System

## Overview
The analyzer module now includes structured threat classification with confidence scoring and detailed threat indicators.

## What Was Added

### 1. CATEGORY_RULES Dictionary
**Location:** [app/analyzer.py](app/analyzer.py#L12-L67)

Defines 8 threat categories with:
- **Keywords**: Set of indicator words for each category
- **Weight**: Priority multiplier (higher = more important)
- **Score Boost**: Additional threat score if matched

**Categories:**
- `Illegal Marketplace` - Shop/market/drugs/weapons (weight: 3.0)
- `Financial/Crypto` - Crypto/blockchain/wallet (weight: 2.0)
- `Hacking/Exploitation` - Exploits/malware/ransomware (weight: 3.5)
- `Data Leak` - Database dumps/credentials (weight: 3.0)
- `Fraud` - Scams/phishing/money laundering (weight: 2.5)
- `Communication/Forum` - Forums/chat/discussions (weight: 1.0)
- `Document/Info` - Documents/guides/archives (weight: 1.2)
- `Adult Content` - Explicit/18+/escort (weight: 1.5)

### 2. NEW: classify_threat() Function
**Location:** [app/analyzer.py](app/analyzer.py#L145-L245)

**Purpose:** Advanced classification with confidence scoring

**Input:**
```python
classify_threat(
    keywords,              # List of extracted keywords
    crypto_addresses,      # List of crypto addresses found
    emails,               # List of emails found
    clamav_detected=False # Boolean for malware detection
)
```

**Output:**
```python
{
    "category": "Illegal Marketplace",        # Best-matched category
    "confidence": 0.78,                       # Confidence score (0-1)
    "threat_indicators": {
        "keyword_matches": 3,                 # Count of matched keywords
        "matched_keywords": ["shop", ...],    # Top 5 keywords
        "crypto_detected": true,
        "email_detected": true,
        "malware_detected": false
    }
}
```

**Confidence Calculation:**
- Keyword matches: +0.15 per match (max 0.5)
- Crypto address detected: +0.25
- Email address detected: +0.10
- Malware detected (ClamAV): +0.15
- Generic content: 0.30 (default minimum)
- Maximum: 0.99 (never 100% certain)

### 3. MODIFIED: analyze_content() Function
**Location:** [app/analyzer.py](app/analyzer.py#L248-L291)

**Enhancement:** Now includes classification data

**New Input Parameter:**
```python
clamav_detected=False  # Optional, defaults to False
```

**New Output Fields:**
```python
{
    # Existing fields
    "content_hash": "...",
    "emails_found": [...],
    "crypto_addresses": [...],
    "threat_score": 45,
    "risk_level": "MEDIUM",
    
    # NEW classification fields
    "category": "Financial/Crypto",
    "confidence": 0.75,
    "threat_indicators": {
        "keyword_matches": 2,
        "matched_keywords": ["bitcoin", "wallet"],
        "crypto_detected": true,
        "email_detected": false,
        "malware_detected": false
    }
}
```

### 4. Risk Level Mapping
**Location:** [app/analyzer.py](app/analyzer.py#L105-L138)

Maps threat score to human-readable severity:
- **LOW**: 0-30 points
- **MEDIUM**: 31-70 points
- **HIGH**: 71-100 points

## Data Flow

```
Scrape HTML
    ↓
Parse (extract text, keywords)
    ↓
analyze_content() called with:
  - text
  - keywords
  - clamav_detected (optional)
    ↓
Inside analyze_content():
  1. Extract emails & crypto addresses
  2. Calculate threat_score
  3. Call classify_threat()
  4. Determine risk_level
  5. Return complete analysis
    ↓
Store in MongoDB + File Analysis
```

## MongoDB Storage Example

Your MongoDB document now contains:

```json
{
  "_id": ObjectId("..."),
  "url": "http://example.onion/",
  "title": "Example Site",
  
  "threat_score": 45,
  "risk_level": "MEDIUM",
  "category": "Financial/Crypto",
  "confidence": 0.78,
  
  "threat_indicators": {
    "keyword_matches": 3,
    "matched_keywords": ["bitcoin", "wallet", "transaction"],
    "crypto_detected": true,
    "email_detected": false,
    "malware_detected": false
  },
  
  "emails_found": [],
  "crypto_addresses": ["1A1z7agoat..."],
  
  "clamav_detected": false,
  "clamav_details": null,
  
  "file_analysis": [...],
  "content_changed": false,
  "timestamp": ISODate("2026-02-21T13:40:24.233Z")
}
```

## Database Queries for Intelligence

```javascript
// Find high-confidence threats
db.collection('sites').find({ 
  "confidence": { $gte: 0.8 },
  "category": "Illegal Marketplace"
})

// Find crypto-related sites
db.collection('sites').find({ 
  "threat_indicators.crypto_detected": true
})

// Get threat statistics by category
db.collection('sites').aggregate([
  { $match: { "confidence": { $gte: 0.7 } } },
  { $group: { 
    _id: "$category", 
    count: { $sum: 1 },
    avg_confidence: { $avg: "$confidence" }
  }}
])

// Monitor for malware detections
db.collection('sites').find({ 
  "threat_indicators.malware_detected": true
})
```

## Benefits of This Implementation

✅ **Structured Intelligence** - Clear categorization based on threat profiles
✅ **Confidence Scoring** - Know how certain the classification is
✅ **Detailed Indicators** - Track exactly which signals triggered the classification
✅ **Risk Levels** - Human-readable severity assessment
✅ **Extensible** - Easy to add new categories or adjust weights
✅ **No Breaking Changes** - Backward compatible with existing pipeline
✅ **Database Native** - All data stored in MongoDB for querying

## Example Usage

```python
from app.analyzer import analyze_content, classify_threat

# Basic usage
result = analyze_content(
    text="Buy bitcoin at our secure wallet",
    keywords=["buy", "bitcoin", "wallet"]
)

print(f"Category: {result['category']}")           # Financial/Crypto
print(f"Threat Score: {result['threat_score']}")   # 50
print(f"Risk Level: {result['risk_level']}")       # MEDIUM
print(f"Confidence: {result['confidence']}")       # 0.78

# With ClamAV detection
result = analyze_content(
    text="...",
    keywords=[...],
    clamav_detected=True  # Malware found
)
```

## Future Enhancements

Potential improvements:
1. Machine learning-based confidence scoring
2. Dynamic category rules based on threat landscape
3. Integration with threat intelligence feeds (VirusTotal, MISP)
4. Custom rules per organization
5. Temporal analysis (how threat level changes over time)
6. Correlation with known threat actors/groups
