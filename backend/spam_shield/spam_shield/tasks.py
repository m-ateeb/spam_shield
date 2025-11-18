# spam_shield/tasks.py (FINAL UPDATED with Module 4 - Decision Engine)
import base64
import requests
from email_connector.oauth_utils import get_valid_access_token
from email_connector.email_validator import validate_email_authenticity
from email_connector.db_utils import (
    syslog,
    get_account_by_email,
    upsert_connected_account,
)
from email_connector.models import Email, EmailAuthResult, URLAnalysis, ConnectedAccount
from django.contrib.auth.models import User
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
            syslog("account_not_found", "process_incoming_email", {"email": email})
            return
        
        # 🆕 Use token refresh mechanism
        access_token = get_valid_access_token(account)
        if not access_token:
            syslog("token_refresh_failed", "process_incoming_email", {"email": email})
            return

        if provider == "gmail":
            process_gmail(email, access_token, account, history_id)
        else:
            process_outlook(email, access_token, account)
    except Exception as e:
        syslog("task_error", "process_incoming_email", {"error": str(e)})
        raise self.retry(exc=e)


# ===========================
# Initial Email Scan Task
# ===========================
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_initial_emails(self, account_id: int):
    """
    Scan the 50 most recent emails when a Gmail account is first connected.
    This runs once per account connection.
    """
    try:
        account_obj = ConnectedAccount.objects.filter(id=account_id, provider='gmail').first()
        if not account_obj:
            syslog("account_not_found", "scan_initial_emails", {"account_id": account_id})
            return
        
        email = account_obj.email_address
        account = get_account_by_email(email, "gmail")
        if not account:
            syslog("account_not_found", "scan_initial_emails", {"email": email})
            return
        
        # Get valid access token
        access_token = get_valid_access_token(account)
        if not access_token:
            syslog("token_refresh_failed", "scan_initial_emails", {"email": email})
            raise self.retry(exc=Exception("Token refresh failed"))
        
        # Fetch 50 most recent emails
        url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        syslog("initial_scan_started", "scan_initial_emails", {
            "email": email,
            "account_id": account_id
        })
        
        # Fetch messages in batches to get 50 total
        all_message_ids = []
        page_token = None
        max_results = 50
        
        while len(all_message_ids) < max_results:
            params = {"maxResults": min(50, max_results - len(all_message_ids))}
            if page_token:
                params["pageToken"] = page_token
            
            resp = requests.get(url, headers=headers, params=params, timeout=30).json()
            messages = resp.get("messages", [])
            
            if not messages:
                break
            
            all_message_ids.extend([msg["id"] for msg in messages])
            
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        
        # Process each email
        processed_count = 0
        for msg_id in all_message_ids[:max_results]:
            try:
                msg_data = requests.get(f"{url}/{msg_id}", headers=headers, timeout=30).json()
                save_email(msg_data, account)
                processed_count += 1
            except Exception as e:
                syslog("initial_scan_message_error", "scan_initial_emails", {
                    "message_id": msg_id,
                    "error": str(e)
                })
        
        syslog("initial_scan_complete", "scan_initial_emails", {
            "email": email,
            "account_id": account_id,
            "processed_count": processed_count,
            "total_fetched": len(all_message_ids)
        })
        
    except Exception as e:
        syslog("initial_scan_error", "scan_initial_emails", {
            "account_id": account_id,
            "error": str(e)
        })
        raise self.retry(exc=e)



# ===========================
# MODULE 1 → Gmail / Outlook Fetch
# ===========================
def process_gmail(email, token, account, history_id=None):
    """
    Fetch Gmail messages and process each.
    
    Args:
        email: Email address
        token: Access token
        account: Account dictionary
        history_id: Optional history ID for incremental updates (from Gmail push notifications)
    """
    url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    
    # If history_id is provided, use Gmail history API for incremental updates
    if history_id:
        try:
            history_url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/history"
            history_params = {
                "startHistoryId": history_id,
                "historyTypes": ["messageAdded"],
                "maxResults": 50
            }
            history_resp = requests.get(history_url, headers=headers, params=history_params, timeout=30).json()
            
            # Extract message IDs from history
            message_ids = set()
            for history_record in history_resp.get("history", []):
                for msg_added in history_record.get("messagesAdded", []):
                    message_ids.add(msg_added["message"]["id"])
            
            # Process each new message
            for msg_id in message_ids:
                try:
                    msg_data = requests.get(f"{url}/{msg_id}", headers=headers, timeout=30).json()
                    save_email(msg_data, account)
                except Exception as e:
                    syslog("gmail_message_fetch_error", "process_gmail", {
                        "message_id": msg_id,
                        "error": str(e)
                    })
            return
        except Exception as e:
            syslog("gmail_history_error", "process_gmail", {
                "history_id": history_id,
                "error": str(e)
            })
            # Fall through to regular fetch if history API fails
    
    # Regular fetch for initial scan or fallback
    batch_size = getattr(settings, 'EMAIL_BATCH_SIZE', 10)
    resp = requests.get(url, headers=headers, params={"maxResults": batch_size}, timeout=30).json()
    for msg in resp.get("messages", []):
        try:
            msg_data = requests.get(f"{url}/{msg['id']}", headers=headers, timeout=30).json()
            save_email(msg_data, account)
        except Exception as e:
            syslog("gmail_message_fetch_error", "process_gmail", {
                "message_id": msg.get("id"),
                "error": str(e)
            })


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
    """Extract, validate, scan, and store email details in database."""
    message_id = raw_msg.get("id")
    if not message_id:
        return

    # === FETCH FULL RAW EMAIL (for DKIM/SPF) ===
    raw_email = b""
    from email_connector.db_utils import decrypt_token
    access_token = decrypt_token(account['access_token'])
    
    if account["provider"] == "gmail":
        try:
            raw_url = f"https://gmail.googleapis.com/gmail/v1/users/{account['email_address']}/messages/{message_id}?format=raw"
            headers = {"Authorization": f"Bearer {access_token}"}
            raw_resp = requests.get(raw_url, headers=headers).json()
            raw_email_b64 = raw_resp.get("raw", "")
            if raw_email_b64:
                raw_email_b64 += "=" * (-len(raw_email_b64) % 4)
                raw_email = base64.urlsafe_b64decode(raw_email_b64)
        except Exception as e:
            syslog("raw_email_fetch_error", "save_email", {"provider": "gmail", "error": str(e)})
    
    # 🆕 NEW: Fetch raw MIME for Outlook
    elif account["provider"] == "outlook":
        try:
            raw_url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/$value"
            headers = {"Authorization": f"Bearer {access_token}"}
            raw_resp = requests.get(raw_url, headers=headers, timeout=10)
            if raw_resp.status_code == 200:
                raw_email = raw_resp.content
        except Exception as e:
            syslog("raw_email_fetch_error", "save_email", {"provider": "outlook", "error": str(e)})

    # === VALIDATE EMAIL AUTHENTICITY ===
    sender = extract_sender(raw_msg)
    domain = sender.split("@")[-1] if "@" in sender else ""
    auth_result = validate_email_authenticity(raw_email, domain, message_id)

    # === EXTRACT HEADERS ===
    headers = {}
    if account["provider"] == "gmail":
        headers = {h["name"]: h["value"] for h in raw_msg.get("payload", {}).get("headers", [])}
    elif account["provider"] == "outlook":
        # Outlook provides direct fields
        headers = {
            "Subject": raw_msg.get("subject", ""),
            "From": raw_msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            "Reply-To": raw_msg.get("replyTo", [{}])[0].get("emailAddress", {}).get("address", "") if raw_msg.get("replyTo") else "",
        }

    # === SAVE EMAIL TO DATABASE (emails table) ===
    try:
        # Check if email already exists (to avoid duplicate processing)
        existing_email = Email.objects.filter(message_id=message_id).first()
        if existing_email:
            syslog("email_already_exists", "save_email", {"message_id": message_id})
            return  # Email already processed, skip
        
        # Get user and account objects
        user = User.objects.get(id=int(account["user_id"]))
        account_obj = ConnectedAccount.objects.get(id=account["id"])
        
        # Parse received_at
        from dateutil.parser import parse
        received_at_str = raw_msg.get("internalDate") if account["provider"] == "gmail" else raw_msg.get("receivedDateTime")
        received_at = None
        if received_at_str:
            if isinstance(received_at_str, (int, float)):
                from datetime import datetime
                received_at = datetime.fromtimestamp(received_at_str / 1000)
            else:
                received_at = parse(received_at_str)
        
        body_html = extract_body_html(raw_msg)
        
        # Create email object
        try:
            email_obj = Email.objects.create(
                user=user,
                account=account_obj,
                message_id=message_id,
                subject=headers.get("Subject", ""),
                sender=sender,
                from_header=headers.get("From", ""),
                reply_to=headers.get("Reply-To", "") or None,
                return_path=headers.get("Return-Path", "") or None,
                body_html=body_html,
                highlighted_body_html=highlight_urls(body_html),
                received_at=received_at,
                spf_result=auth_result["spf_result"],
                dkim_result=auth_result["dkim_result"],
                dmarc_policy=auth_result["dmarc_policy"],
                auth_score=auth_result["auth_score"],
                is_suspicious=False,  # Don't mark as suspicious until full analysis is complete
            )
            email_id = email_obj.id
        except Exception as e:
            # Handle IntegrityError (duplicate) or other database errors
            from django.db import IntegrityError
            if isinstance(e, IntegrityError) and 'message_id' in str(e).lower():
                syslog("email_duplicate_skipped", "save_email", {"message_id": message_id})
                return  # Duplicate email, skip processing
            raise  # Re-raise if it's a different error

        # === INSERT AUTHENTICATION RESULTS ===
        EmailAuthResult.objects.create(
            email=email_obj,
            spf_status=auth_result["spf_result"],
            dkim_status=auth_result["dkim_result"],
            dmarc_status=auth_result["dmarc_policy"],
            validation_summary=auth_result.get("validation_summary", ""),
        )

        # === EXTRACT & ANALYZE EMBEDDED URLs ===
        try:
            urls = extract_urls_from_html(body_html)
            for url in urls:
                url_result = analyze_url(url, email_id)  # Pass email_id for async polling
                URLAnalysis.objects.create(
                    email=email_obj,
                    url=url,
                    source="body",
                    google_safebrowsing=url_result.get("google_safebrowsing"),
                    urlhaus_status=url_result.get("urlhaus_status"),
                    urlscan_status=url_result.get("urlscan_status"),
                    final_verdict=url_result.get("final_verdict", "safe"),
                )
        except Exception as e:
            syslog("url_analysis_error", "save_email", {"email_id": email_id, "error": str(e)})
    except Exception as e:
        syslog("email_insert_error", "save_email", {"message_id": message_id, "error": str(e)})
        return

    # === RUN NEXT PIPELINE (Module 4) ===
    run_post_process_pipeline.delay(email_id)


# ===========================
# MODULE 4 → Decision Engine
# ===========================
@shared_task
def run_post_process_pipeline(email_id: int):
    """
    Run post-processing pipeline:
    Step 1: Wait for URL analysis to complete
    Step 2: Decision Engine (Module 4)
    """
    from spam_shield.decision_engine import run_rule_based_classification
    try:
        # Check if URL analysis is complete before running classification
        email_obj = Email.objects.filter(id=email_id).first()
        if not email_obj:
            syslog("pipeline_error", "run_post_process_pipeline", {"email_id": email_id, "error": "Email not found"})
            return
        
        # Check for pending URL analysis
        url_analyses = URLAnalysis.objects.filter(email=email_obj)
        url_results = [u.final_verdict for u in url_analyses]
        url_pending = url_results.count("pending")
        
        # If URLs are still being analyzed, do NOT run classification yet
        if len(url_results) > 0 and url_pending > 0:
            syslog("pipeline_deferred", "run_post_process_pipeline", {
                "email_id": email_id, 
                "pending_urls": url_pending,
                "message": "Classification deferred - URL analysis still in progress"
            })
            return  # Exit without running classification
        
        # Run classification only when analysis is complete
        result = run_rule_based_classification(email_id)
        if result:
            syslog("pipeline_complete", "run_post_process_pipeline", {"email_id": email_id, "result": result})
        else:
            syslog("pipeline_incomplete", "run_post_process_pipeline", {"email_id": email_id, "message": "Classification returned None"})
    except Exception as e:
        syslog("pipeline_error", "run_post_process_pipeline", {"email_id": email_id, "error": str(e)})
