# spam_shield/tasks.py (FINAL UPDATED with Module 4 - Decision Engine)
import base64
import requests
from email_connector.email_validator import validate_email_authenticity
from email_connector.supabase_client import (
    supabase,
    decrypt_token,
    syslog,
    get_account_by_email,
    upsert_connected_account,
)
from email_connector.utils import extract_sender, extract_body_html, highlight_urls
from email_connector.url_reputation import extract_urls_from_html, analyze_url
from django.conf import settings
from celery import shared_task


# ===========================
# MODULE 1 → Entry Task
# ===========================
@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def process_incoming_email(self, email: str, provider: str, history_id=None):
    """Entry task — triggers Gmail/Outlook email processing."""
    try:
        account = get_account_by_email(email, provider)
        if not account:
            return
        access_token = decrypt_token(account["access_token"])
        if not access_token:
            return

        if provider == "gmail":
            process_gmail(email, access_token, account, history_id)
        else:
            process_outlook(email, access_token, account)
    except Exception as e:
        syslog("task_error", "process_incoming_email", {"error": str(e)})
        raise self.retry(exc=e)


# ===========================
# MODULE 1 → Gmail / Outlook Fetch
# ===========================
def process_gmail(email, token, account, history_id):
    """Fetch recent Gmail messages and process each."""
    url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params={"maxResults": 10}).json()
    for msg in resp.get("messages", []):
        msg_data = requests.get(f"{url}/{msg['id']}", headers=headers).json()
        save_email(msg_data, account)


def process_outlook(email, token, account):
    """Fetch Outlook messages and process each."""
    url = "https://graph.microsoft.com/v1.0/me/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers).json()
    for msg in resp.get("value", []):
        save_email(msg, account)


# ===========================
# MODULE 2 & 3 → Email Validation + URL Reputation
# ===========================
def save_email(raw_msg, account):
    """Extract, validate, scan, and store email details in Supabase."""
    message_id = raw_msg.get("id")
    if not message_id:
        return

    # === FETCH FULL RAW EMAIL (for DKIM/SPF) ===
    raw_email = b""
    if account["provider"] == "gmail":
        try:
            raw_url = f"https://gmail.googleapis.com/gmail/v1/users/{account['email_address']}/messages/{message_id}?format=raw"
            headers = {"Authorization": f"Bearer {decrypt_token(account['access_token'])}"}
            raw_resp = requests.get(raw_url, headers=headers).json()
            raw_email_b64 = raw_resp.get("raw", "")
            if raw_email_b64:
                raw_email_b64 += "=" * (-len(raw_email_b64) % 4)
                raw_email = base64.urlsafe_b64decode(raw_email_b64)
        except Exception as e:
            syslog("raw_email_fetch_error", "save_email", {"error": str(e)})

    # === VALIDATE EMAIL AUTHENTICITY ===
    sender = extract_sender(raw_msg)
    domain = sender.split("@")[-1] if "@" in sender else ""
    auth_result = validate_email_authenticity(raw_email, domain, message_id)

    # === EXTRACT HEADERS ===
    headers = {h["name"]: h["value"] for h in raw_msg.get("payload", {}).get("headers", [])}

    # === SAVE EMAIL TO SUPABASE (emails table) ===
    email_row = {
        "user_id": account["user_id"],
        "account_id": account["id"],
        "message_id": message_id,
        "subject": headers.get("Subject", ""),
        "sender": sender,
        "from_header": headers.get("From", ""),
        "reply_to": headers.get("Reply-To", ""),
        "return_path": headers.get("Return-Path", ""),
        "body_html": extract_body_html(raw_msg),
        "highlighted_body_html": highlight_urls(extract_body_html(raw_msg)),
        "received_at": raw_msg.get("internalDate"),
        "spf_result": auth_result["spf_result"],
        "dkim_result": auth_result["dkim_result"],
        "dmarc_policy": auth_result["dmarc_policy"],
        "auth_score": auth_result["auth_score"],
        "is_suspicious": auth_result["auth_score"] < 60,
    }

    res = supabase.table("emails").insert(email_row).execute()
    if not res.data:
        syslog("email_insert_error", "save_email", {"message_id": message_id})
        return

    email_id = res.data[0]["id"]

    # === INSERT AUTHENTICATION RESULTS (email_auth_results table) ===
    supabase.table("email_auth_results").insert(
        {
            "email_id": email_id,
            "spf_status": auth_result["spf_result"],
            "dkim_status": auth_result["dkim_result"],
            "dmarc_status": auth_result["dmarc_policy"],
            "validation_summary": auth_result["validation_summary"],
        }
    ).execute()

    # === EXTRACT & ANALYZE EMBEDDED URLs (url_analysis table) ===
    try:
        urls = extract_urls_from_html(email_row["body_html"])
        for url in urls:
            url_result = analyze_url(url)
            supabase.table("url_analysis").insert(
                {
                    "email_id": email_id,
                    "url": url,
                    "source": "body",
                    "google_safebrowsing": url_result.get("google_safebrowsing"),
                    "phishtank_status": url_result.get("phishtank_status"),
                    "urlscan_status": url_result.get("urlscan_status"),
                    "final_verdict": url_result.get("final_verdict"),
                }
            ).execute()
    except Exception as e:
        syslog("url_analysis_error", "save_email", {"email_id": email_id, "error": str(e)})

    # === RUN NEXT PIPELINE (Module 4) ===
    run_post_process_pipeline.delay(email_id)


# ===========================
# MODULE 4 → Decision Engine
# ===========================
@shared_task
def run_post_process_pipeline(email_id: int):
    """
    Run post-processing pipeline:
    Step 1: Decision Engine (Module 4)
    """
    from spam_shield.decision_engine import run_rule_based_classification
    try:
        result = run_rule_based_classification(email_id)
        if result:
            syslog("pipeline_complete", "run_post_process_pipeline", {"email_id": email_id, "result": result})
    except Exception as e:
        syslog("pipeline_error", "run_post_process_pipeline", {"email_id": email_id, "error": str(e)})
