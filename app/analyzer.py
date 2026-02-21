"""
Analyzer Module
Performs crypto detection, email detection,
content hashing, threat scoring, and advanced threat classification
"""

import re
import hashlib
import unicodedata
from app.utils import logger
from app.logger import log_threat_detection

# ============================================================================
# CATEGORY RULES - Define classification logic for threat categories
# ============================================================================
CATEGORY_RULES = {
    "Illegal Marketplace": {
        "keywords": {
            "shop", "store", "buy", "sell", "vendor", "market", "product",
            "drugs", "weapon", "exploit", "stolen", "illegal", "contraband",
            "escrow", "carding", "cvv"
        },
        "weight": 3.7,  # Priority multiplier
        "score_boost": 35  # Additional threat score if matched
    },
    "Financial/Crypto": {
        "keywords": {
            "bitcoin", "crypto", "wallet", "payment", "transaction", "money",
            "ethereum", "monero", "zcash", "blockchain", "exchange",
            "mining", "coin"
        },
        "weight": 1.6,
        "score_boost": 25
    },
    "Hacking/Exploitation": {
        "keywords": {
            "hack", "exploit", "vulnerability", "malware", "ransomware",
            "ddos", "botnet", "zero-day", "payload", "breach", "intrusion",
            "worm", "trojan", "keylogger", "remote access", "database",
            "carding", "dump", "cvv"
        },
        "weight": 3.8,
        "score_boost": 40
    },
    "Data Leak": {
        "keywords": {
            "leak", "leaked", "database", "dump", "credentials", "password",
            "breach", "exposed", "confidential", "classified", "documents",
            "personal data", "records", "user data"
        },
        "weight": 3.4,
        "score_boost": 38
    },
    "Fraud": {
        "keywords": {
            "fraud", "scam", "phishing", "forgery", "fake", "counterfeit",
            "money laundering", "ponzi", "scheme", "clone", "impersonate",
            "spoof", "identity theft"
        },
        "weight": 2.5,
        "score_boost": 30
    },
    "Communication/Forum": {
        "keywords": {
            "forum", "chat", "message", "contact", "email", "discuss",
            "community", "board", "thread", "post", "group", "channel"
        },
        "weight": 1.0,
        "score_boost": 5
    },
    "Document/Info": {
        "keywords": {
            "document", "guide", "manual", "tutorial", "information",
            "research", "whitepaper", "pdf", "archive", "collection",
            "library", "reference"
        },
        "weight": 1.2,
        "score_boost": 3
    },
    "Adult Content": {
        "keywords": {
            "adult", "explicit", "nsfw", "sex", "porn", "xxx", "18+",
            "escort", "prostitution", "dating", "cam"
        },
        "weight": 1.5,
        "score_boost": 8
    }
}

# ============================================================================
# RISK LEVEL THRESHOLDS
# ============================================================================
RISK_THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (31, 70),
    "HIGH": (71, 100)
}


def normalize_text(text):
    """Normalize text to improve indicator extraction."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    # Remove zero-width, formatting, and soft-hyphen characters that break regex boundaries
    text = re.sub(r"[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]", "", text)
    text = text.replace("\xa0", " ")
    return text


def detect_emails(text):
    # Strict boundaries without relying on \b which can fail with unicode
    cleaned_text = normalize_text(text)
    cleaned_text = re.sub(r"\s*@\s*", "@", cleaned_text)
    cleaned_text = re.sub(r"\s*\.\s*", ".", cleaned_text)
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    emails = re.findall(email_pattern, cleaned_text)
    return list(set(emails))


def detect_crypto_addresses(text):
    crypto_addresses = []
    cleaned_text = normalize_text(text)

    # Bitcoin legacy (base58)
    btc_legacy_pattern = r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"
    crypto_addresses.extend(re.findall(btc_legacy_pattern, cleaned_text))

    # Bitcoin bech32
    btc_bech32_pattern = r"\bbc1[0-9a-z]{25,62}\b"
    crypto_addresses.extend(re.findall(btc_bech32_pattern, cleaned_text))

    # Ethereum addresses
    eth_pattern = r"\b0x[a-fA-F0-9]{40}\b"
    crypto_addresses.extend(re.findall(eth_pattern, cleaned_text))

    # Monero standard + integrated (95 or 106 chars, starts with 4 or 8)
    xmr_pattern = r"\b[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93,105}\b"
    crypto_addresses.extend(re.findall(xmr_pattern, cleaned_text))

    return list(set(crypto_addresses))


def hash_content(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def calculate_threat_score(emails, crypto_addresses, keywords, text):
    """Threat scoring with clearer weighting"""
    score = 0
    keywords_lower = set(kw.lower() for kw in keywords)
    text_lower = (text or "").lower()

    if crypto_addresses:
        score += 30

    if emails:
        score += 20

    suspicious_keywords = {
        "ransomware", "dump", "carding", "escrow", "exploit", "malware",
        "hack", "drugs", "weapon", "leak", "fraud", "stolen", "illegal"
    }

    # Count unique matches across keywords list and full text
    matches = {kw for kw in suspicious_keywords if kw in keywords_lower or kw in text_lower}
    score += len(matches) * 10

    return min(score, 100)


def get_risk_level(threat_score):
    """Convert threat score to meaningful risk level"""
    if threat_score < 30:
        return "LOW"
    if threat_score <= 60:
        return "MEDIUM"
    return "HIGH"


def classify_threat(keywords, crypto_addresses, emails, clamav_detected=False):
    """
    Advanced threat classification with confidence scoring
    
    Args:
        keywords: List of extracted keywords
        crypto_addresses: List of detected crypto addresses
        emails: List of detected email addresses
        clamav_detected: Boolean indicating malware detection
    
    Returns:
        dict: {
            "category": str,
            "confidence": float (0-1),
            "threat_indicators": dict
        }
    """
    keyword_set = set(kw.lower() for kw in keywords)
    force_marketplace = {"escrow", "carding"}.issubset(keyword_set)
    
    # Track all matches for confidence calculation
    category_matches = {}
    
    # Scan keywords against all category rules
    for category_name, rules in CATEGORY_RULES.items():
        category_keywords = set(kw.lower() for kw in rules["keywords"])
        matches = keyword_set.intersection(category_keywords)
        
        if matches:
            match_count = len(matches)
            weighted_score = match_count * rules["weight"]
            category_matches[category_name] = {
                "match_count": match_count,
                "matched_keywords": list(matches),
                "weighted_score": weighted_score
            }
    
    # If no keyword matches, check for crypto indicators
    if not category_matches and crypto_addresses:
        category_matches["Financial/Crypto"] = {
            "match_count": 1,
            "matched_keywords": ["crypto_detected"],
            "weighted_score": 2.0
        }
    
    # If no matches yet, default to Communication
    if not category_matches:
        category_matches["Communication/Forum"] = {
            "match_count": 0,
            "matched_keywords": [],
            "weighted_score": 0.5
        }
    
    # Select category with highest weighted score
    best_category = max(
        category_matches.items(),
        key=lambda x: x[1]["weighted_score"]
    )[0]
    
    # Confidence based on keyword coverage within the chosen category
    matched_count = category_matches[best_category]["match_count"]
    category_keyword_count = len(CATEGORY_RULES[best_category]["keywords"])
    if category_keyword_count == 0:
        confidence = 0.0
    else:
        confidence = min(0.99, matched_count / category_keyword_count)
    
    output_category = "Marketplace" if force_marketplace else best_category

    return {
        "category": output_category,
        "confidence": round(confidence, 2),
        "threat_indicators": {
            "keyword_matches": category_matches[best_category]["match_count"],
            "matched_keywords": category_matches[best_category]["matched_keywords"][:5],  # Top 5
            "crypto_detected": bool(crypto_addresses),
            "email_detected": bool(emails),
            "malware_detected": clamav_detected
        }
    }


def analyze_content(text, keywords=None, clamav_detected=False):
    """
    Comprehensive content analysis with threat classification
    
    Args:
        text: Text content to analyze
        keywords: List of extracted keywords
        clamav_detected: Boolean indicating if malware was detected
    
    Returns:
        dict: Analysis results with threat score, category, confidence, and risk level
    """
    if keywords is None:
        keywords = []

    # Extract threat indicators
    normalized_text = normalize_text(text)
    emails = detect_emails(normalized_text)
    if not emails and "@" in normalized_text:
        candidates = re.findall(r"\S+@\S+", normalized_text)
        if candidates:
            logger.warning(f"Email candidates found but regex did not match: {candidates[:5]}")
    crypto_addresses = detect_crypto_addresses(normalized_text)
    content_hash = hash_content(normalized_text)

    # Expand keywords with known category terms found in full text
    expanded_keywords = set(kw.lower() for kw in keywords)
    text_lower = (normalized_text or "").lower()
    for rules in CATEGORY_RULES.values():
        for term in rules["keywords"]:
            if term in text_lower:
                expanded_keywords.add(term)

    expanded_keywords_list = list(expanded_keywords)
    threat_score = calculate_threat_score(emails, crypto_addresses, expanded_keywords_list, text)
    
    # Perform advanced threat classification
    classification = classify_threat(
        expanded_keywords_list,
        crypto_addresses,
        emails,
        clamav_detected
    )
    
    # Determine risk level from threat score
    risk_level = get_risk_level(threat_score)
    
    # Log threat detection for high-risk content
    if threat_score > 50:
        log_threat_detection(
            url="[analyzing]",  # URL will be logged by main.py
            threat_score=threat_score,
            category=classification["category"],
            risk_level=risk_level
        )

    return {
        "content_hash": content_hash,
        "emails_found": emails,
        "crypto_addresses": crypto_addresses,
        "threat_score": threat_score,
        "category": classification["category"],
        "confidence": classification["confidence"],
        "threat_indicators": classification["threat_indicators"],
        "risk_level": risk_level
    }