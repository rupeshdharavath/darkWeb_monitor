# Intelligence Monitoring Platform - Alert Engine & IOC Correlation

## System Architecture

Your DarkWeb Monitor is now a **fully operational intelligence monitoring platform** with:
- ✅ **Alert Engine** - Real-time threat detection and alerting
- ✅ **IOC Correlation** - Track and detect reused threat indicators
- ✅ **Three MongoDB Collections** - scraped_data, alerts, iocs

## PART 1: ALERT ENGINE

### How It Works

The alert engine automatically triggers notifications when:
1. **High Threat Score** (> 60/100)
2. **Malware Detected** (ClamAV positive)
3. **Content Changed** (URL content modified)
4. **IOC Reuse** (Indicators appear on multiple URLs)

### Collections & Data Flow

**triggers** → **checks conditions** → **inserts to alerts** → **stored in MongoDB**

### Alert Collection Structure

```javascript
db.alerts.insertOne({
  "_id": ObjectId(...),
  "url": "http://example.onion/",
  "reason": "High Threat Score (75/100)",
  "threat_score": 75,
  "category": "Illegal Marketplace",
  "confidence": 0.82,
  "severity": "HIGH",
  "status": "new",
  "timestamp": ISODate("2026-02-21T13:40:24.233Z"),
  "details": {
    "threat_reason": "Threat score exceeds threshold: 75"
  }
})
```

### Implementation Details

#### database.py - New Methods

**1. `insert_alert(alert_data)`**
```python
db_manager.insert_alert({
    "url": url,
    "reason": "High Threat Score (75/100)",
    "threat_score": 75,
    "category": "Illegal Marketplace",
    "severity": "HIGH",
    "details": {...}
})
```

**2. Alert Triggers in main.py**

**Trigger 1: Threat Score**
```python
if threat_score > 60:
    alert_triggered = True
    alert_reason = f"High Threat Score ({threat_score}/100)"
```

**Trigger 2: Malware Detection**
```python
if clamav_detected:
    alert_triggered = True
    alert_reason = "🚨 MALWARE DETECTED"
```

**Trigger 3: Content Changed**
```python
if content_changed:
    alert_triggered = True
    alert_reason = "Content Change Detected"
```

### Query Alerts

```javascript
// Get all new alerts
db.alerts.find({ "status": "new" })

// Find high-severity alerts
db.alerts.find({ "severity": "HIGH" })

// Get malware detection alerts
db.alerts.find({ "reason": { $regex: "MALWARE" } })

// Get alerts by category
db.alerts.find({ "category": "Illegal Marketplace" })

// Alert statistics
db.alerts.aggregate([
  { $group: { 
    _id: "$severity", 
    count: { $sum: 1 }
  }}
])
```

---

## PART 2: IOC CORRELATION ENGINE

### What is IOC Correlation?

**IOC = Indicator of Compromise** (email, crypto address, file hash)

**Correlation** = Detecting when the same indicator appears across multiple URLs

**Why it matters**: Single indicator on multiple URLs = **organized threat activity**

### IOC Types Tracked

1. **Email Addresses**
   - Detected: automatic extraction from page text
   - Alert: User re-uses same email across sites
   - Severity: HIGH

2. **Crypto Addresses**
   - Detected: automatic extraction (Bitcoin, Monero, Ethereum)
   - Alert: Same wallet address across multiple marketplaces
   - Severity: HIGH

3. **File Hashes**
   - Detected: SHA256 hash of all downloaded files
   - Alert: Same file distributed across multiple URLs
   - Severity: MEDIUM

### IOC Collection Structure

```javascript
db.iocs.insertOne({
  "_id": ObjectId(...),
  "ioc_value": "admin@example.com",           // The actual indicator
  "ioc_type": "email",                        // Type: email|crypto|file_hash
  "url": "http://site1.onion/",               // Where it was found
  "timestamp": ISODate("2026-02-21T13:40:24.233Z")
})

// When same email appears on another site, another doc is inserted
db.iocs.insertOne({
  "ioc_value": "admin@example.com",
  "ioc_type": "email",
  "url": "http://site2.onion/",  // Same email, different URL
  "timestamp": ISODate("2026-02-21T13:41:00.000Z")
})
```

### Implementation Details

#### database.py - New Methods

**1. `check_ioc_reuse(ioc_value, ioc_type)`**
```python
result = db_manager.check_ioc_reuse("admin@example.com", "email")
# Returns:
# {
#   "exists": True,
#   "first_seen": timestamp,
#   "urls": ["http://site1.onion/", "http://site2.onion/"],
#   "reuse_count": 2
# }
```

**2. `insert_ioc(ioc_value, ioc_type, url)`**
```python
reuse_info = db_manager.insert_ioc("1A1z7agoatXwv...", "crypto", url)

if reuse_info and reuse_info["exists"]:
    print(f"Alert: Crypto address used on {reuse_info['reuse_count']} URLs")
```

#### main.py - IOC Tracking

**Email Tracking**
```python
for email in emails_found:
    reuse_info = db_manager.insert_ioc(email, "email", url)
    if reuse_info and reuse_info["exists"]:
        # Auto-generate HIGH severity alert
        db_manager.insert_alert({
            "reason": "IOC Reuse Detected - Email",
            "ioc_value": email,
            "reuse_count": reuse_info["reuse_count"],
            "severity": "HIGH"
        })
```

**Crypto Tracking**
```python
for crypto_addr in crypto_addresses:
    reuse_info = db_manager.insert_ioc(crypto_addr, "crypto", url)
    if reuse_info and reuse_info["exists"]:
        # Auto-generate HIGH severity alert
        db_manager.insert_alert({
            "reason": "IOC Reuse Detected - Crypto Address",
            "ioc_value": crypto_addr,
            "reuse_count": reuse_info["reuse_count"],
            "severity": "HIGH"
        })
```

**File Hash Tracking**
```python
for file_hash in file_hashes:
    reuse_info = db_manager.insert_ioc(file_hash, "file_hash", url)
    if reuse_info and reuse_info["exists"]:
        # Auto-generate MEDIUM severity alert
        db_manager.insert_alert({
            "reason": "IOC Reuse Detected - File Hash",
            "ioc_value": file_hash,
            "reuse_count": reuse_info["reuse_count"],
            "severity": "MEDIUM"
        })
```

### Query IOCs

```javascript
// Find all emails tracked
db.iocs.find({ "ioc_type": "email" })

// Find crypto addresses
db.iocs.find({ "ioc_type": "crypto" })

// Find how many times an email was used
db.iocs.countDocuments({ 
  "ioc_value": "admin@example.com",
  "ioc_type": "email"
})

// Get all URLs for a specific IOC
db.iocs.find({ 
  "ioc_value": "admin@example.com",
  "ioc_type": "email"
}).project({ "url": 1 })

// Find IOCs found on >2 URLs (suspicious reuse)
db.iocs.aggregate([
  { $group: { 
    _id: { value: "$ioc_value", type: "$ioc_type" },
    count: { $sum: 1 },
    urls: { $push: "$url" }
  }},
  { $match: { count: { $gte: 2 } } }
])
```

---

## Complete Workflow

```
Scrape URL
  ↓
Parse (extract text, keywords, emails, crypto)
  ↓
Analyze (detect threats, classify category, calculate confidence)
  ↓
Download Files (if any)
  ↓
Scan Files (ClamAV, forensic analysis)
  ↓
Store in scraped_data collection
  ↓
Check Alert Conditions:
  ├─ Threat Score > 60? → Alert
  ├─ Malware Detected? → Alert
  └─ Content Changed? → Alert
  ↓
Track IOCs (emails, crypto, file hashes)
  ├─ Check: Email exists before? → If yes → HIGH Alert
  ├─ Check: Crypto address exists before? → If yes → HIGH Alert
  └─ Check: File hash exists before? → If yes → MEDIUM Alert
  ↓
Store in alerts collection (if triggered)
Store in iocs collection
  ↓
Monitor Intelligence Platform Ready
```

---

## Example Real-World Scenario

### Scenario: Criminal Email Network

**Day 1 - URL A:**
```
Scrape: marketplace.onion
Found: admin@criminalgroup.com
Action: Insert IOC
Result: First occurrence, no alert
```

**Day 2 - URL B:**
```
Scrape: forum.onion
Found: admin@criminalgroup.com
Action: Check IOC → REUSE DETECTED!
Result: Create HIGH alert with:
  - IOC: admin@criminalgroup.com
  - Reuse count: 2
  - Previous URL: marketplace.onion
  - Current URL: forum.onion
Alert: "IOC Reuse Detected - Email (admin@criminalgroup.com found on 2 URLs)"
```

**Day 3 - URL C:**
```
Scrape: leaks.onion
Found: admin@criminalgroup.com
Action: Check IOC → MAJOR REUSE!
Result: Create HIGH alert with:
  - IOC: admin@criminalgroup.com
  - Reuse count: 3
  - All URLs: [marketplace.onion, forum.onion, leaks.onion]
Alert: "IOC Reuse Detected - Email (admin@criminalgroup.com found on 3 URLs)"
```

**Intelligence Conclusion**: Same criminal operating across 3 platforms

---

## Database Collections Summary

| Collection | Purpose | Key Fields |
|-----------|---------|-----------|
| `scraped_data` | All analyzed pages | url, threat_score, category, confidence, emails_found, crypto_addresses, clamav_detected |
| `alerts` | Threat notifications | url, reason, severity, threat_score, status |
| `iocs` | Indicator tracking | ioc_value, ioc_type (email/crypto/file_hash), url |

---

## Monitoring Capabilities

Your system can now:

✅ **Real-Time Alerts**
- High-risk content detection
- Malware notifications
- Content change tracking

✅ **Threat Intelligence**
- Link threat actors across sites
- Identify organized groups
- Track malware distribution

✅ **Correlation Analysis**
- Email address networks
- Crypto payment tracking
- File distribution patterns

✅ **Autonomous Monitoring**
- Continuous 24/7 operation
- Automatic alert generation
- Self-updating threat database

---

## Log Examples

When system runs, you'll see:

```
🚨 ALERT TRIGGERED: High Threat Score (75/100) - http://market.onion/
🚨 ALERT TRIGGERED: 🚨 MALWARE DETECTED - http://files.onion/
🔄 IOC REUSE DETECTED: email found on 2 URLs
🔄 CRYPTO REUSE ALERT: Address found on 3 URLs
🔄 FILE HASH REUSE: Same file on 2 URLs
```

---

## Next Steps

Your platform now has:
1. ✅ Signature-based malware detection (ClamAV)
2. ✅ Advanced threat classification
3. ✅ Real-time alert engine
4. ✅ IOC correlation engine

This is a **professional SOC-level threat monitoring system**.

For further enhancements:
- Email notifications for alerts
- Webhook integrations to SIEM
- Machine learning threat scoring
- Integration with VirusTotal/MISP feeds
- Custom alert rules
