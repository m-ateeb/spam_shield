"""
Classification rules and thresholds
"""
from typing import Dict, List, Tuple

# Known legitimate domains
KNOWN_LEGITIMATE_DOMAINS = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 
    'protonmail.com', 'aol.com', 'mail.com', 'zoho.com', 'yandex.com',
    'netflix.com', 'amazon.com', 'microsoft.com', 'google.com', 'apple.com',
    'facebook.com', 'twitter.com', 'linkedin.com', 'github.com', 'paypal.com'
]


def count_auth_results(spf: str, dkim: str, dmarc: str) -> Dict[str, int]:
    """Count authentication results"""
    auth_results = [spf, dkim, dmarc]
    return {
        'failures': sum(1 for s in auth_results if s in ["fail", "reject", "quarantine"]),
        'passes': sum(1 for s in auth_results if s == "pass"),
        'unknown': sum(1 for s in auth_results if s in ["unknown", "none"]),
    }


def count_url_results(url_analyses) -> Dict[str, int]:
    """Count URL analysis results"""
    url_results = [u.final_verdict for u in url_analyses]
    return {
        'pending': url_results.count("pending"),
        'safe': url_results.count("safe"),
        'suspicious': url_results.count("suspicious"),
        'malicious': url_results.count("malicious"),
        'total': len(url_results),
    }


def is_known_legitimate_domain(sender: str) -> bool:
    """Check if sender domain is known legitimate"""
    sender_domain = sender.split('@')[-1] if '@' in sender else ''
    return sender_domain.lower() in KNOWN_LEGITIMATE_DOMAINS


def classify_by_malicious_urls(url_malicious: int) -> Tuple[str, str, str, float]:
    """Classify email with malicious URLs"""
    if url_malicious > 0:
        confidence = min(95.0, 85.0 + (url_malicious * 3.0))
        return "phishing", "delete", f"Malicious URLs detected ({url_malicious} malicious URL(s))", confidence
    return None, None, None, 0.0


def classify_by_auth_score(auth_score: int, auth_counts: Dict, spf: str, dkim: str, dmarc: str) -> Tuple[str, str, str, float]:
    """Classify email based on authentication score"""
    if auth_score < 20:
        confidence = min(95.0, 80.0 + ((20 - auth_score) * 0.75))
        reason = f"Very low authenticity score ({auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        return "phishing", "delete", reason, confidence
    elif auth_score < 40:
        confidence = 65.0 + ((40 - auth_score) * 1.0)
        reason = f"Low authenticity score ({auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        return "suspicious", "quarantine", reason, confidence
    else:
        confidence = 75.0 + ((auth_score - 40) * 0.33)
        reason = f"Passed authenticity checks (Score: {auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        return "safe", "allow", reason, confidence

