# DarkWeb Monitor

A Python-based tool for monitoring and scraping dark web sites through the Tor network, with data storage in MongoDB Atlas.

## Features

- **Tor Integration**: Anonymous scraping through Tor network
- **Web Scraping**: Automated content extraction from .onion sites
- **Data Parsing**: Extract titles, links, and keywords from scraped content
- **MongoDB Storage**: Store scraped data in MongoDB Atlas cloud database
- **Logging**: Comprehensive logging for monitoring and debugging

## Project Structure

```
darkweb-monitor/
│
├── venv/                     # Virtual environment
│
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration settings
│   ├── tor_proxy.py         # Tor proxy session management
│   ├── scraper.py           # Web scraping logic
│   ├── parser.py            # HTML parsing and data extraction
│   ├── database.py          # MongoDB Atlas integration
│   └── utils.py             # Utility functions
│
├── data/
│   └── sample_output.json   # Sample output format
│
├── logs/
│   └── app.log              # Application logs
│
├── .env                     # Environment variables (MongoDB URI)
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Prerequisites

- Python 3.8 or higher
- Tor Browser or Tor service running on your machine
- MongoDB Atlas account (free tier available)

## Installation

1. **Clone or download the project**

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB Atlas**:
   - Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a new cluster
   - Get your connection string
   - Update `.env` file with your MongoDB URI:
     ```
     MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
     ```

5. **Install and start Tor**:
   - **Linux**: `sudo apt-get install tor && sudo service tor start`
   - **Mac**: `brew install tor && brew services start tor`
   - **Windows**: Download and run Tor Browser

## Configuration

Edit `app/config.py` to customize:
- Tor proxy settings
- Request timeout and delays
- Logging configuration
- Database settings

## Usage

1. **Add target URLs** in `main.py`:
   ```python
   urls_to_scrape = [
       "http://example.onion",
       # Add more .onion URLs
   ]
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **View logs**:
   ```bash
   tail -f logs/app.log
   ```

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

## Troubleshooting

### Tor Connection Issues
- Ensure Tor service is running: `sudo service tor status`
- Check if port 9050 is available: `netstat -an | grep 9050`
- Verify proxy settings in `config.py`

### Database Connection Issues
- Verify MongoDB Atlas URI in `.env`
- Check network connectivity
- Ensure IP whitelist in MongoDB Atlas includes your IP

### Scraping Failures
- Some sites may block automated access
- Check logs for specific error messages
- Adjust delays between requests
- Verify Tor connection is working

## Development

To contribute or modify:

1. Follow PEP 8 style guidelines
2. Add docstrings to all functions
3. Update requirements.txt when adding dependencies
4. Test thoroughly before committing changes

## License

This project is provided as-is for educational purposes.

## Disclaimer

The developers are not responsible for any misuse of this tool. Users are solely responsible for ensuring their use complies with all applicable laws and regulations.
# darkWeb_monitor
