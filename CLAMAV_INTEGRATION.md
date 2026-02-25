# ClamAV Integration Guide

## Overview
This document describes the ClamAV signature-based malware detection integration added to the DarkWeb Monitor system.

## What Was Added

### 1. **file_analyzer.py** - New `analyze_with_clamav()` Function
- **Location**: [backend/app/file_analyzer.py](backend/app/file_analyzer.py)
- **Functionality**: 
  - Connects to ClamAV daemon (clamd) using pyclamd library
  - Performs signature-based malware scanning on downloaded files
  - Returns detailed threat information including threat names and types
  - Handles graceful degradation if ClamAV is not available

- **Return Structure**:
  ```python
  {
      "clamav_status": "connected|not_installed|not_running|error",
      "clamav_detected": bool,
      "threats": [
          {
              "file": "filename.exe",
              "threat_type": "Trojan.Generic",
              "threat_name": "Win.Trojan.Generic-12345"
          }
      ],
      "error": "error message (if any)"
  }
  ```

### 2. **file_analyzer.py** - Updated `analyze_file()` Function
- Now runs ClamAV scan on all downloaded files
- Automatically extracts `clamav_status` and `clamav_detected` fields
- Stores complete ClamAV response in results for detailed analysis

### 3. **database.py** - MongoDB Field Extraction
- Extracts ClamAV results from file analysis and stores at document level:
  - `clamav_status`: Overall ClamAV connection status
  - `clamav_detected`: Boolean flag if any malware was detected
  - `clamav_details`: Detailed threat information for each infected file
- Aggregates results across all files analyzed for a URL
- Enables easy querying and alerting in MongoDB

### 4. **requirements.txt** - New Dependency
- Added `pyclamd==0.4.0` for Python ClamAV daemon communication

## Installation & Setup

### Prerequisites
- Linux/Kali Linux system (recommended)
- Root/sudo access for ClamAV installation

### Step 1: Install ClamAV
```bash
# On Debian/Ubuntu/Kali Linux
sudo apt-get update
sudo apt-get install clamav clamav-daemon clamav-freshclam

# Start ClamAV daemon
sudo service clamav-daemon start

# Verify ClamAV is running
sudo service clamav-daemon status
```

### Step 2: Install Python Dependencies
```bash
# From workspace root
pip install -r backend/requirements.txt

# Or specifically:
pip install pyclamd==0.4.0
```

### Step 3: Update ClamAV Signatures (Recommended)
```bash
# Update virus definitions (requires ~100-200MB)
sudo freshclam

# Enable automatic updates
sudo systemctl enable clamav-freshclam
```

### Step 4: Verify Installation
```python
# Test ClamAV connectivity
import pyclamd
clam = pyclamd.ClamD()
print(clam.ping())  # Should return True
```

## Features

### ✅ Automatic Malware Detection
- Every downloaded file is automatically scanned
- Results stored in MongoDB for historical analysis
- Works seamlessly with existing file analysis pipeline

### ✅ Graceful Degradation
- If pyclamd library not installed: Reports "not_installed" status
- If ClamAV daemon not running: Reports "not_running" status
- If connection error: Reports "error" status
- System continues operating without ClamAV if unavailable

### ✅ Detailed Threat Information
```python
# Example MongoDB document with ClamAV data:
{
    "_id": ObjectId(...),
    "url": "https://example.com",
    "clamav_status": "connected",
    "clamav_detected": True,
    "clamav_details": [
        {
            "file": "malware.exe",
            "threats": [
                {
                    "file": "malware.exe",
                    "threat_type": "Trojan.Generic",
                    "threat_name": "Win.Trojan.Generic-12345"
                }
            ]
        }
    ],
    "file_analysis": [
        {
            "file_name": "malware.exe",
            "analysis": {
                "clamav_status": "connected",
                "clamav_detected": True,
                "clamav": {
                    "clamav_status": "connected",
                    "clamav_detected": True,
                    "threats": [...]
                }
            }
        }
    ]
}
```

## Usage Examples

### Real-time Monitoring
```python
# When the system detects malware:
# 1. Logs warning: 🚨 MALWARE DETECTED: Win.Trojan.Generic-12345
# 2. Stores details in MongoDB
# 3. Increments threat_score if needed
# 4. Flags file for quarantine (future enhancement)
```

### Database Queries
```javascript
// MongoDB: Find URLs with detected malware
db.collection.find({ "clamav_detected": true })

// Find specific threat types
db.collection.find({ "clamav_details.threats.threat_name": /Trojan/ })

// Get threat statistics
db.collection.aggregate([
    { $match: { "clamav_detected": true } },
    { $group: { _id: "$clamav_detected", count: { $sum: 1 } } }
])
```

## Performance Considerations

- **First Scan Time**: ClamAV may take longer on first scan due to signature loading
- **File Size Limits**: Default downloader limits files to 50MB (configurable)
- **Timeout**: File analysis has 30-second timeout per tool
- **Daemon Memory**: ClamAV daemon uses ~200-400MB RAM (variable)

### Optimization Tips
1. Run freshclam during off-peak hours to update signatures
2. Use ClamAV's multithreading: `--max-threads=4` in clamd.conf
3. Consider increasing timeout if slowdowns occur:
    - Edit: `ANALYSIS_TIMEOUT` in [backend/app/file_analyzer.py](backend/app/file_analyzer.py)

## Troubleshooting

### ClamAV Daemon Not Starting
```bash
# Check logs
sudo tail -f /var/log/clamav/clamd.log

# Restart daemon
sudo service clamav-daemon restart

# Manual start for debugging
sudo clamd
```

### Connection Refused Error
```bash
# Verify daemon is running
sudo systemctl status clamav-daemon

# Check socket file
ls -la /var/run/clamav/clamd.ctl

# Ensure permissions
sudo usermod -aG clamav $USER
# (Logout and login for changes to take effect)
```

### Memory Issues
```bash
# Monitor ClamAV memory usage
watch -n 1 'ps aux | grep clamd'

# Reduce MaxFileSize in clamd.conf if needed
sudo nano /etc/clamav/clamd.conf
```

### Signature Updates Not Working
```bash
# Manual update
sudo freshclam

# Check freshclam config
cat /etc/clamav/freshclam.conf

# Run freshclam with verbose output
sudo freshclam -v
```

## Integration with Existing System

The ClamAV integration is **non-breaking** and automatically integrated into:
1. **File Download Pipeline**: Each downloaded file is scanned
2. **Database Storage**: Results stored in MongoDB alongside other analysis
3. **Threat Scoring**: Can trigger threat score adjustments (future enhancement)
4. **Logging**: All scans logged with emoji indicators for quick scanning

## Future Enhancements

Potential improvements for future versions:
1. Automatic quarantine of detected malware
2. Email/webhook alerts for threat detection
3. ClamAV custom rules and yara rules integration
4. Distributed scanning for large-scale deployments
5. False positive management and whitelisting
6. Integration with VirusTotal API for secondary checking

## File Locations

- **Main Integration**: [backend/app/file_analyzer.py](backend/app/file_analyzer.py#L246)
- **Database Storage**: [backend/app/database.py](backend/app/database.py#L76)
- **Dependencies**: [backend/requirements.txt](backend/requirements.txt)
- **Downloader**: [backend/app/downloader.py](backend/app/downloader.py)
- **Main Pipeline**: [backend/main.py](backend/main.py#L100)

## Logs & Monitoring

Watch for these log messages to monitor ClamAV activity:

```
🦠 Running ClamAV malware scan on filename.exe     # Scan started
✅ ClamAV daemon connected                          # Connection successful
✅ ClamAV scan complete: No threats detected        # Clean file
🚨 MALWARE DETECTED: Win.Trojan.Generic-12345      # Threat found
⚠️ ClamAV daemon (clamd) not running                # Daemon issue
⚠️ pyclamd not installed, skipping ClamAV analysis  # Library missing
```

## Support

For issues or questions:
1. Check ClamAV logs: `sudo tail -f /var/log/clamav/clamd.log`
2. Verify daemon status: `sudo service clamav-daemon status`
3. Test Python connectivity: `python -c "import pyclamd; print(pyclamd.ClamD().ping())"`
4. Update signatures: `sudo freshclam`
