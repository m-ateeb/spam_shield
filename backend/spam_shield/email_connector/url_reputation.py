# email_connector/url_reputation.py
import os
import re
import requests
import time
from dotenv import load_dotenv
from email_connector.supabase_client import syslog

load_dotenv()

SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY")
URLHAUS_API_KEY = os.getenv("URLHAUS_API_KEY")  
URLSCAN_API_KEY = os.getenv("URLSCAN_API_KEY") 

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key="
URLHAUS_ENDPOINT = "https://urlhaus-api.abuse.ch/v1/url/"
URLSCAN_ENDPOINT = "https://urlscan.io/api/v1/scan/"

# ===================================================
# =============== HELPER FUNCTIONS ==================
# ===================================================

def extract_urls_from_html(html_content):
    """Extract all URLs from HTML content using regex."""
    if not html_content:
        return []
    url_pattern = r'https?://[^\s"<>]+'
    urls = list(set(re.findall(url_pattern, html_content)))
    return urls


# ===================================================
# =============== SAFE BROWSING CHECK ===============
# ===================================================
def check_google_safe_browsing(url):
    """Check URL against Google Safe Browsing API."""
    if not SAFE_BROWSING_API_KEY:
        syslog("missing_api_key", "check_google_safe_browsing", {"msg": "No Safe Browsing key found"})
        return "unknown"

    try:
        body = {
            "client": {"clientId": "inboxguardian", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        resp = requests.post(
            SAFE_BROWSING_ENDPOINT + SAFE_BROWSING_API_KEY,
            json=body,
            timeout=10
        )
        data = resp.json()
        if "matches" in data:
            return "malicious"
        return "safe"
    except Exception as e:
        syslog("safebrowsing_error", "check_google_safe_browsing", {"url": url, "error": str(e)})
        return "unknown"


# ===================================================
# ================= URLHAUS CHECK ===================
# ===================================================
def check_urlhaus(url):
    """Query URLHaus to see if a URL is flagged as malicious."""
    try:
        headers = {}
        if URLHAUS_API_KEY:
            headers["Auth-Key"] = URLHAUS_API_KEY

        resp = requests.post(
            URLHAUS_ENDPOINT,
            headers=headers,
            data={"url": url},
            timeout=10
        )
        data = resp.json()

        # Example response: {"query_status":"ok","url_status":"online","threat":"malware_download"}
        if data.get("query_status") == "ok":
            return "malicious"
        elif data.get("query_status") in ["no_results", "invalid_url"]:
            return "safe"
        else:
            return "unknown"
    except Exception as e:
        syslog("urlhaus_error", "check_urlhaus", {"url": url, "error": str(e)})
        return "unknown"

# ===================================================
# ================= URLSCAN CHECK ===================
# ===================================================
def check_urlscan(url):
    """Optional deep scan using URLScan.io sandbox and fetch final verdict."""
    if not URLSCAN_API_KEY:
        return "skipped"

    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": URLSCAN_API_KEY   # ✅ Correct header name (lowercase)
        }

        body = {
            "url": url,
            "visibility": "unlisted",    # Default safe mode (not public)
            "country": "de",             # You can randomize or keep fixed
            "tags": ["automated", "email-scan"]
        }

        # === Submit scan ===
        resp = requests.post(URLSCAN_ENDPOINT, json=body, headers=headers, timeout=20)
        if resp.status_code != 200:
            if resp.status_code == 429:
                time.sleep(5)
                return "retry"
            return "error"

        data = resp.json()
        scan_id = data.get("uuid")
        if not scan_id:
            return "error"

        # === Wait for scan result (polling) ===
        result_url = f"https://urlscan.io/api/v1/result/{scan_id}/"
        time.sleep(10)  # wait before polling
        result_resp = requests.get(result_url, headers=headers, timeout=20)

        if result_resp.status_code == 200:
            result_data = result_resp.json()

            # Optional: check for verdicts
            verdicts = result_data.get("verdicts", {})
            overall = verdicts.get("overall", {})
            score = overall.get("score", 0)
            malicious = overall.get("malicious", False)

            if malicious or score > 50:
                return "malicious"
            elif score > 20:
                return "suspicious"
            else:
                return "safe"
        else:
            return "pending"

    except Exception as e:
        syslog("urlscan_error", "check_urlscan", {"url": url, "error": str(e)})
        return "error"


# ===================================================
# ================= MAIN ANALYZER ===================
# ===================================================
def analyze_url(url):

    # === STEP 1: Google Safe Browsing ===
    gsb_result = check_google_safe_browsing(url)
    if gsb_result == "malicious":
        return {
            "google_safebrowsing": "malicious",
            "urlhaus_status": "skipped",
            "urlscan_status": "skipped",
            "final_verdict": "malicious"
        }

    # === STEP 2: URLHaus ===
    urlhaus_result = check_urlhaus(url)
    if urlhaus_result == "malicious":
        return {
            "google_safebrowsing": gsb_result,
            "urlhaus_status": "malicious",
            "urlscan_status": "skipped",
            "final_verdict": "malicious"
        }

    # === STEP 3: URLScan (optional sandboxing) ===
    if gsb_result == "unknown" or urlhaus_result == "unknown":
        scan_status = check_urlscan(url)
        return {
            "google_safebrowsing": gsb_result,
            "urlhaus_status": urlhaus_result,
            "urlscan_status": scan_status,
            "final_verdict": "suspicious" if scan_status == "submitted" else "safe"
        }

    # === FINAL VERDICT ===
    return {
        "google_safebrowsing": gsb_result,
        "urlhaus_status": urlhaus_result,
        "urlscan_status": "skipped",
        "final_verdict": "safe"
    }
