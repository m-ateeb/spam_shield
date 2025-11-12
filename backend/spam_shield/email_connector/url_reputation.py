# email_connector/url_reputation.py
import os
import re
import requests
import time
from celery import shared_task
from dotenv import load_dotenv
from email_connector.db_utils import syslog
from email_connector.models import URLAnalysis

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
def check_urlscan(url, email_id=None):
    """Submit URL to URLScan.io and trigger async polling."""
    if not URLSCAN_API_KEY:
        return "skipped"

    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": URLSCAN_API_KEY
        }

        body = {
            "url": url,
            "visibility": "unlisted",
            "country": "de",
            "tags": ["automated", "email-scan"]
        }

        resp = requests.post(URLSCAN_ENDPOINT, json=body, headers=headers, timeout=20)
        if resp.status_code != 200:
            if resp.status_code == 429:
                return "rate_limited"
            return "error"

        data = resp.json()
        scan_id = data.get("uuid")
        if not scan_id:
            return "error"

        # 🆕 Trigger async polling task
        if email_id:
            poll_urlscan_result.apply_async(args=[scan_id, email_id, url], countdown=15)
        
        return "pending"

    except Exception as e:
        syslog("urlscan_error", "check_urlscan", {"url": url, "error": str(e)})
        return "error"



# ===================================================
# ================= MAIN ANALYZER ===================
# ===================================================
def analyze_url(url, email_id=None):
    """Main URL analyzer with email_id for async polling."""
    gsb_result = check_google_safe_browsing(url)
    if gsb_result == "malicious":
        return {
            "google_safebrowsing": "malicious",
            "urlhaus_status": "skipped",
            "urlscan_status": "skipped",
            "final_verdict": "malicious"
        }

    urlhaus_result = check_urlhaus(url)
    if urlhaus_result == "malicious":
        return {
            "google_safebrowsing": gsb_result,
            "urlhaus_status": "malicious",
            "urlscan_status": "skipped",
            "final_verdict": "malicious"
        }

    if gsb_result == "unknown" or urlhaus_result == "unknown":
        scan_status = check_urlscan(url, email_id)  # 🆕 Pass email_id
        return {
            "google_safebrowsing": gsb_result,
            "urlhaus_status": urlhaus_result,
            "urlscan_status": scan_status,
            "final_verdict": "pending" if scan_status == "pending" else "safe"
        }

    return {
        "google_safebrowsing": gsb_result,
        "urlhaus_status": urlhaus_result,
        "urlscan_status": "skipped",
        "final_verdict": "safe"
    }

@shared_task(bind=True, max_retries=3)
def poll_urlscan_result(self, scan_id: str, email_id: int, url: str):
    """
    Poll URLScan.io for scan results (async task).
    Called after initial submission returns pending.
    """
    try:
        result_url = f"https://urlscan.io/api/v1/result/{scan_id}/"
        headers = {"api-key": URLSCAN_API_KEY} if URLSCAN_API_KEY else {}
        
        result_resp = requests.get(result_url, headers=headers, timeout=20)
        
        if result_resp.status_code == 404:
            # Not ready yet, retry after 15 seconds
            raise self.retry(countdown=15)
        
        if result_resp.status_code == 200:
            result_data = result_resp.json()
            
            # Extract verdict
            verdicts = result_data.get("verdicts", {})
            overall = verdicts.get("overall", {})
            score = overall.get("score", 0)
            malicious = overall.get("malicious", False)
            
            if malicious or score > 50:
                final_verdict = "malicious"
            elif score > 20:
                final_verdict = "suspicious"
            else:
                final_verdict = "safe"
            
            # Update database
            URLAnalysis.objects.filter(
                email_id=email_id,
                url=url
            ).update(
                urlscan_status=final_verdict,
                final_verdict=final_verdict
            )
            
            syslog("urlscan_complete", "poll_urlscan_result", {
                "email_id": email_id, "url": url, "verdict": final_verdict
            })
            
            # Re-run classification ONLY if all URLs are now complete
            try:
                from email_connector.models import Email
                email_obj = Email.objects.filter(id=email_id).first()
                if email_obj:
                    # Check if all URLs are now complete
                    url_analyses = URLAnalysis.objects.filter(email=email_obj)
                    url_results = [u.final_verdict for u in url_analyses]
                    url_pending = url_results.count("pending")
                    
                    # Only run classification if all URLs are complete
                    if url_pending == 0:
                        from spam_shield.decision_engine import run_rule_based_classification
                        result = run_rule_based_classification(email_id)
                        if result:
                            syslog("reclassification_complete", "poll_urlscan_result", {
                                "email_id": email_id, "result": result
                            })
                    else:
                        syslog("reclassification_deferred", "poll_urlscan_result", {
                            "email_id": email_id, "pending_urls": url_pending,
                            "message": "Still waiting for other URL analyses to complete"
                        })
            except Exception as e:
                syslog("reclassification_error", "poll_urlscan_result", {
                    "email_id": email_id, "error": str(e)
                })
            
    except Exception as e:
        syslog("urlscan_poll_error", "poll_urlscan_result", {
            "email_id": email_id, "url": url, "error": str(e)
        })
        raise self.retry(exc=e)