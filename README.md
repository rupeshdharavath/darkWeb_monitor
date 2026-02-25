# DarkWeb Monitor - Threat Intelligence Platform

A comprehensive threat intelligence platform for monitoring and analyzing dark web sites through the Tor network. Features automated content extraction, malware detection, threat scoring, and a modern React dashboard with scan history tracking.

## 🚀 Features

### Core Capabilities
- **🔒 Tor Integration**: Anonymous scraping through Tor network (SOCKS5 proxy)
- **🕸️ Web Scraping**: Automated content extraction from .onion sites
- **🎯 Threat Intelligence**: Advanced threat scoring and risk classification
- **🦠 Malware Detection**: Integrated ClamAV scanning for downloaded files
- **📊 Real-time Analytics**: Live threat indicators and behavioral markers
- **📜 Scan History**: Track all scans with searchable history
- **🔍 Content Analysis**: Extract emails, crypto addresses, PGP keys, and keywords
- **📁 File Analysis**: Download and analyze files with multiple tools (strings, exiftool, binwalk)
- **🗄️ MongoDB Storage**: Cloud-based data storage with MongoDB Atlas
- **📝 Comprehensive Logging**: System and alert logs for monitoring

### Intelligence Features
- **Threat Scoring**: Automated risk assessment (0-100 scale)
- **Category Classification**: Auto-categorize sites (marketplace, forum, etc.)
- **Content Change Detection**: Track modifications using SHA-256 hashing
- **IOC Tracking**: Monitor indicators of compromise (emails, crypto, hashes)
- **Status Detection**: Real-time availability monitoring
- **PGP Detection**: Identify encrypted communications
- **Keyword Matching**: Detect threat-related terms

### Security Tools Integration
- **ClamAV**: Malware signature scanning
- **strings**: Readable string extraction
- **exiftool**: Metadata analysis
- **binwalk**: Firmware and hidden file detection

## 📁 Project Structure

```
darkweb-monitor/
│
├── .venv/                         # Python virtual environment
│
├── backend/
│   ├── app/                       # Core Python modules
│   │   ├── analyzer.py           # Threat analysis engine
│   │   ├── config.py             # Configuration settings
│   │   ├── database.py           # MongoDB operations
│   │   ├── downloader.py         # File download handler
│   │   ├── file_analyzer.py      # Security tool integrations
│   │   ├── logger.py             # Logging system
│   │   ├── parser.py             # HTML content parser
│   │   ├── scraper.py            # Web scraping engine
│   │   ├── tor_proxy.py          # Tor connection handler
│   │   └── utils.py              # Utility functions
│   │
│   ├── data/                      # Sample data and downloads
│   ├── logs/                      # System and alert logs
│   ├── .env                       # Environment variables
│   ├── main.py                    # CLI pipeline
│   ├── server.py                  # Flask API server
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── CategoryPieChart.jsx
│   │   │   ├── Header.jsx        # Navigation header
│   │   │   ├── Loader.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── StatusCard.jsx
│   │   │   ├── ThreatBarChart.jsx
│   │   │   ├── ThreatScoreCard.jsx
│   │   │   └── TimelineChart.jsx
│   │   │
│   │   ├── pages/                # Page components
│   │   │   ├── Dashboard.jsx     # Main dashboard
│   │   │   └── History.jsx       # Scan history page
│   │   │
│   │   ├── services/
│   │   │   └── api.js            # API service layer
│   │   │
│   │   ├── App.jsx               # Router setup
│   │   ├── main.jsx              # Entry point
│   │   └── index.css             # Styles
│   │
│   ├── .env                       # Frontend config
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js        # Tailwind CSS config
│   └── vite.config.js            # Vite config
│
└── README.md

## 📋 Prerequisites

- **Python 3.8+** (tested with 3.13)
- **Node.js 16+** and npm
- **Tor service** running on port 9050
- **MongoDB Atlas** account (free tier available)
- **Security Tools** (optional but recommended):
  - ClamAV (`sudo apt install clamav clamav-daemon`)
  - exiftool (`sudo apt install libimage-exiftool-perl`)
  - binwalk (`sudo apt install binwalk`)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/rupeshdharavath/darkWeb_monitor.git
cd darkWeb_monitor
```

### 2. Backend Setup

**Create virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows
```

**Install dependencies:**
```bash
pip install -r backend/requirements.txt
```

**Configure environment variables:**
Create `backend/.env`:
```env
# MongoDB Atlas Configuration
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/darkweb_monitor?appName=darkwebCluster

# Database Settings
DATABASE_NAME=darkweb_monitor
COLLECTION_NAME=scraped_data

# Application Settings
LOG_LEVEL=INFO
```

### 3. Frontend Setup

**Install dependencies:**
```bash
cd frontend
npm install
```

**Configure API endpoint:**
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Tor Setup

**Install and start Tor:**
```bash
# Kali Linux / Debian / Ubuntu
sudo apt install tor
sudo systemctl start tor
sudo systemctl enable tor

# Verify Tor is running on port 9050
ss -tlnp | grep 9050
```

### 5. Security Tools (Optional)

**Install analysis tools:**
```bash
sudo apt update
sudo apt install clamav clamav-daemon libimage-exiftool-perl binwalk

# Update ClamAV virus definitions
sudo freshclam
```

## 🚀 Usage

### Start the Backend (Flask API)
```bash
cd backend
source ../.venv/bin/activate
python server.py
```
Backend runs on: **http://localhost:8000**

### Start the Frontend (Vite + React)
```bash
cd frontend
npm run dev
```
Frontend runs on: **http://localhost:5173**

### Access the Application
Open your browser and navigate to:
```
http://localhost:5173
```

## 🎯 Using the Dashboard

### Main Dashboard
1. Enter an `.onion` URL in the search bar
2. Click "Scan" to analyze the site
3. View real-time threat intelligence:
   - Status detection (Online/Offline)
   - Threat score (0-100)
   - Risk level (Low/Medium/High)
   - Extracted data (emails, crypto, keywords)
   - File analysis results
   - Content preview

### Scan History
1. Click **"History"** in the top navigation
2. View all previous scans sorted by newest first
3. Click any entry to view full details
4. Use the **"Back to History"** button to return

### API Endpoints
- `GET /health` - Health check
- `POST /scan` - Scan an onion URL
- `GET /history` - Get all scan history
- `GET /history/:id` - Get specific scan entry

## Important Notes

### Legal and Ethical Considerations

⚠️ **WARNING**: This tool is for educational and research purposes only.

- Always ensure you have permission to scrape websites
- Respect robots.txt files and terms of service
- Be aware of local laws regarding dark web access
- Use responsibly and ethically
- Never use for illegal activities

### Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Use strong MongoDB Atlas credentials
- Regularly update dependencies for security patches
- Monitor your logs for suspicious activity

## ⚙️ Configuration

### Backend Configuration (`backend/app/config.py`)
- **Tor Proxy**: SOCKS5 proxy settings (default: 127.0.0.1:9050)
- **Request Timeout**: Adjust for slow onion sites
- **Delays**: Configure request delays to avoid rate limiting
- **Logging Levels**: INFO, WARNING, ERROR

### Database Collections
- **scraped_data**: Main scan results with full content
- **alerts**: Threat notifications and high-risk detections
- **iocs**: Indicators of compromise tracking

## 🛡️ Security & Threat Detection

### Threat Scoring Algorithm
The system calculates threat scores based on:
- Matched threat keywords
- Cryptocurrency address detection
- Email address patterns
- Malware signatures (ClamAV)
- Content change frequency
- PGP key presence
- Site category classification

### Risk Levels
- **LOW** (0-33): Minimal threat indicators
- **MEDIUM** (34-66): Moderate suspicious activity
- **HIGH** (67-100): Significant threat detected

## 📊 Data Persistence

All scans are stored in MongoDB with:
- Full content snapshots
- SHA-256 content hashing
- Change detection history
- Response time tracking
- File analysis results
- Threat scores over time

Database automatically sorts entries **newest first** for efficient history retrieval.

## 🔍 CLI Usage (Optional)

For batch processing or automation:
```bash
cd backend
source ../.venv/bin/activate
python main.py
```

Edit `main.py` to add target URLs.

## 📝 Logging

Logs are stored in `backend/logs/`:
- **system.log**: General application logs
- **alerts.log**: High-priority threat alerts

View in real-time:
```bash
tail -f backend/logs/system.log
tail -f backend/logs/alerts.log
```

## 🐛 Troubleshooting

### Tor Connection Issues
```bash
# Check Tor status
sudo systemctl status tor

# Restart Tor
sudo systemctl restart tor

# Verify port 9050
ss -tlnp | grep 9050
```

**Error: `[Errno 111] Connection refused`**
- Tor service is not running
- Run: `sudo systemctl start tor`

### Database Connection Issues
- Verify MongoDB URI in `backend/.env`
- Check IP whitelist in MongoDB Atlas (allow 0.0.0.0/0 for testing)
- Test connection: `python backend/test_mongo_connection.py`

### Frontend Not Loading
- Ensure backend is running on port 8000
- Check `frontend/.env` has correct `VITE_API_BASE_URL`
- Clear browser cache and reload

### ClamAV Issues
```bash
# Update virus definitions
sudo freshclam

# Start daemon
sudo systemctl start clamav-daemon
```

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

## 🛠️ Tech Stack

### Backend
- **Python 3.13** - Core language
- **Flask** - REST API framework
- **Flask-CORS** - Cross-origin resource sharing
- **Requests** - HTTP client with Tor proxy support
- **BeautifulSoup4** - HTML parsing
- **pymongo** - MongoDB driver
- **python-dotenv** - Environment management
- **ClamAV** - Malware detection
- **Tor** - Anonymous networking

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Tailwind CSS** - Styling framework

### Database
- **MongoDB Atlas** - Cloud database

### Security Tools
- **ClamAV** - Antivirus scanning
- **exiftool** - Metadata extraction
- **binwalk** - Firmware analysis
- **strings** - String extraction

## 📸 Features Overview

### Dashboard Features
- ✅ Real-time URL scanning
- ✅ Threat score visualization
- ✅ Status detection (Online/Offline/Unknown)
- ✅ Risk level classification
- ✅ PGP detection
- ✅ Content change tracking
- ✅ Keyword extraction
- ✅ Email and crypto address extraction
- ✅ File download and analysis
- ✅ Malware scanning
- ✅ Interactive charts and graphs

### History Features
- ✅ Chronological scan history
- ✅ Quick view of all scans
- ✅ Click to view full details
- ✅ Back navigation
- ✅ Newest first sorting

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines for Python
- Use ESLint/Prettier for JavaScript/React
- Add docstrings to all functions
- Write descriptive commit messages
- Test thoroughly before submitting PR

## 📄 Important Notes

### ⚠️ Legal and Ethical Considerations

**WARNING**: This tool is for **educational and research purposes only**.

- ✅ Use only for legitimate security research
- ✅ Obtain proper authorization before scanning
- ✅ Comply with all applicable laws and regulations
- ✅ Respect website terms of service
- ✅ Follow responsible disclosure practices

- ❌ Do not use for illegal activities
- ❌ Do not scan sites without permission
- ❌ Do not engage in unauthorized access
- ❌ Do not distribute malware or illegal content

**Legal Disclaimer**: Accessing the dark web and scanning websites may be illegal in some jurisdictions. Users are solely responsible for ensuring their activities comply with local, state, and federal laws.

### 🔒 Security Best Practices

1. **Never commit sensitive data**:
   - Keep `.env` files in `.gitignore`
   - Use strong MongoDB credentials
   - Rotate API keys regularly

2. **Keep dependencies updated**:
   ```bash
   pip list --outdated
   npm outdated
   ```

3. **Monitor logs regularly**:
   - Check for suspicious activity
   - Review threat alerts
   - Analyze access patterns

4. **Network security**:
   - Use Tor for anonymity
   - Don't expose backend publicly
   - Use HTTPS in production
   - Implement rate limiting

## 🔮 Future Enhancements

- [ ] User authentication and authorization
- [ ] Scheduled automated scans
- [ ] Email notifications for threats
- [ ] Advanced filtering and search
- [ ] Export reports (PDF/CSV)
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] API rate limiting
- [ ] WebSocket for real-time updates
- [ ] Machine learning threat detection

## 📚 Documentation

Additional documentation files:
- `THREAT_CLASSIFICATION.md` - Threat detection details
- `URL_STATUS_DETECTION.md` - Status detection logic
- `INTELLIGENCE_PLATFORM.md` - Platform architecture
- `LOGGING_SYSTEM.md` - Logging implementation
- `CLAMAV_INTEGRATION.md` - Malware scanning setup

## 🙏 Acknowledgments

- Tor Project for anonymous networking
- MongoDB for cloud database
- ClamAV for malware detection
- Open source community

## 📧 Contact

**Developer**: Rupesh Dharavath  
**GitHub**: [@rupeshdharavath](https://github.com/rupeshdharavath)  
**Repository**: [darkWeb_monitor](https://github.com/rupeshdharavath/darkWeb_monitor)

## 📜 License

This project is provided as-is for educational purposes.

## ⚖️ Disclaimer

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.**

The developers and contributors are not responsible for any misuse, damage, or illegal activities conducted with this tool. Users assume all responsibility and legal liability for their actions. This tool is intended solely for educational, research, and authorized security testing purposes.

By using this software, you agree to use it responsibly and in compliance with all applicable laws and regulations.

---

**⭐ If you find this project helpful, please consider giving it a star on GitHub!**
