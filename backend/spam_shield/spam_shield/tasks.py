from celery import shared_task
import requests, time, re
from email_connector.supabase_client import supabase, decrypt_token, syslog, get_account_by_email, upsert_connected_account
from django.conf import settings

@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def process_incoming_email(self, email: str, provider: str, history_id=None):
    try:
        account = get_account_by_email(email, provider)
        if not account:
            return
        access_token = decrypt_token(account['access_token'])
        if not access_token:
            return

        if provider == "gmail":
            process_gmail(email, access_token, account, history_id)
        else:
            process_outlook(email, access_token, account)
    except Exception as e:
        syslog("task_error", "process_incoming_email", {"error": str(e)})
        raise self.retry(exc=e)

def process_gmail(email, token, account, history_id):
    url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, params={"maxResults": 10}).json()
    for msg in resp.get("messages", []):
        msg_data = requests.get(f"{url}/{msg['id']}", headers=headers).json()
        save_email(msg_data, account)

def process_outlook(email, token, account):
    url = "https://graph.microsoft.com/v1.0/me/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers).json()
    for msg in resp.get("value", []):
        save_email(msg, account)

def save_email(raw_msg, account):
    message_id = raw_msg.get('id')
    if not message_id:
        return
    exists = supabase.table("emails").select("id").eq("message_id", message_id).eq("account_id", account['id']).limit(1).execute()
    if exists.data:
        return

    body_html = extract_body_html(raw_msg)
    highlighted = highlight_urls(body_html)

    email_row = {
        "user_id": account['user_id'],
        "account_id": account['id'],
        "message_id": message_id,
        "subject": raw_msg.get('subject'),
        "sender": extract_sender(raw_msg),
        "body_html": body_html,
        "highlighted_body_html": highlighted,
        "received_at": raw_msg.get('receivedDateTime') or raw_msg.get('internalDate')
    }
    res = supabase.table("emails").insert(email_row).execute()
    if res.data:
        from spam_shield.tasks import run_post_process_pipeline
        run_post_process_pipeline.delay(res.data[0]['id'])

def extract_body_html(msg):
    payload = msg.get('payload', {})
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/html':
            return part.get('body', {}).get('data', '')
    return payload.get('body', {}).get('data', '')

def extract_sender(msg):
    return msg.get('payload', {}).get('headers', [])[-1].get('value', '') if 'payload' in msg else msg.get('from', {}).get('emailAddress', {}).get('address', '')

def highlight_urls(html):
    if not html:
        return html
    urls = re.findall(r'href=[\'"]?([^\'" >]+)', html)
    for url in urls:
        if any(x in url.lower() for x in ['login', 'verify', 'bank']):
            html = html.replace(url, f'<mark style="background:#ff4444;color:white;">{url}</mark>')
    return html