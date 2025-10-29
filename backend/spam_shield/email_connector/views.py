from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests, json, logging, time
from .supabase_client import upsert_connected_account, get_account_by_email, syslog, decrypt_token
from .utils import extract_jwt, get_user_id_from_jwt
from spam_shield.tasks import process_incoming_email

logger = logging.getLogger(__name__)

# ======================
# GOOGLE OAUTH
# ======================
def google_login(request):
    """Redirects user to Google's OAuth consent screen."""
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly "
        f"https://www.googleapis.com/auth/gmail.modify "
        f"https://www.googleapis.com/auth/userinfo.email "
        f"https://www.googleapis.com/auth/userinfo.profile "
        f"openid&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return redirect(auth_url)


def google_callback(request):
    """Handles Google's OAuth callback and links Gmail account under Supabase user."""
    # 🔹 Step 1: Extract JWT from request header
    jwt_token = extract_jwt(request)
    if not jwt_token:
        return JsonResponse({"error": "No JWT provided"}, status=401)

    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return JsonResponse({"error": "Invalid or expired JWT"}, status=401)

    # 🔹 Step 2: Get the authorization code
    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)

    # 🔹 Step 3: Exchange code for access + refresh tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    tokens = requests.post(token_url, data=data, timeout=10).json()

    access_token = tokens.get('access_token')
    if not access_token:
        syslog("oauth_error", "google_callback", {"error": tokens})
        return JsonResponse({"error": "Failed to get access token"}, status=400)

    # 🔹 Step 4: Get Gmail user info
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    ).json()
    email = user_info.get('email')
    if not email:
        return JsonResponse({"error": "No email found"}, status=400)

    # 🔹 Step 5: Store connected Gmail under user_id (NOT user email)
    account_data = {
        "user_id": user_id,
        "email_address": email,
        "provider": "gmail",
        "access_token": access_token,
        "refresh_token": tokens.get('refresh_token'),
        "token_expiry": (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(tokens.get('expires_in', 3600)))
        ).isoformat(),
        "inbox_sync_status": "connected",
    }
    upsert_connected_account(account_data)
    syslog("oauth_connect", "google_callback", {"email": email})

    # 🔹 Step 6: Start Gmail push notifications
    try:
        watch_payload = {
            "topicName": f"projects/{settings.GOOGLE_PROJECT_ID}/topics/gmail-topic"
        }
        watch_resp = requests.post(
            f"https://gmail.googleapis.com/gmail/v1/users/{email}/watch",
            headers={"Authorization": f"Bearer {access_token}"},
            json=watch_payload,
            timeout=10,
        )
        syslog("gmail_watch", "google_callback", {"status": watch_resp.status_code})
    except Exception as e:
        syslog("gmail_watch_error", "google_callback", {"error": str(e)})

    return JsonResponse({"status": "Gmail connected", "email": email})


# ======================
# FETCH RECENT GMAIL
# ======================
@require_GET
def fetch_recent_gmail(request):
    """Fetch last 5 Gmail messages for a connected account."""
    email = request.GET.get("email")
    if not email:
        return JsonResponse({"error": "missing email"}, status=400)

    try:
        account = get_account_by_email(email, "gmail")
        if not account:
            return JsonResponse({"error": "no linked account"}, status=404)

        access_token = decrypt_token(account["access_token"])
        if not access_token:
            return JsonResponse({"error": "invalid token"}, status=401)

        url = f"https://gmail.googleapis.com/gmail/v1/users/{email}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, params={"maxResults": 5}).json()

        messages = []
        for msg in resp.get("messages", []):
            msg_detail = requests.get(f"{url}/{msg['id']}", headers=headers).json()
            snippet = msg_detail.get("snippet", "")
            subject = ""
            for h in msg_detail.get("payload", {}).get("headers", []):
                if h.get("name") == "Subject":
                    subject = h.get("value")
            messages.append({"id": msg["id"], "subject": subject, "snippet": snippet})

        return JsonResponse({"email": email, "messages": messages}, safe=False)
    except Exception as e:
        syslog("gmail_fetch_error", "fetch_recent_gmail", {"error": str(e)})
        return JsonResponse({"error": str(e)}, status=500)


# ======================
# MICROSOFT OAUTH
# ======================
def microsoft_login(request):
    """Redirects to Microsoft OAuth screen."""
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={settings.MICROSOFT_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={settings.MICROSOFT_REDIRECT_URI}&"
        f"scope=User.Read Mail.Read Mail.ReadWrite offline_access openid profile email&"
        f"response_mode=query"
    )
    return redirect(auth_url)


def microsoft_callback(request):
    """Handles Microsoft OAuth callback and links Outlook account."""
    jwt_token = extract_jwt(request)
    if not jwt_token:
        return JsonResponse({"error": "No JWT provided"}, status=401)

    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return JsonResponse({"error": "Invalid JWT"}, status=401)

    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        'code': code,
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'client_secret': settings.MICROSOFT_CLIENT_SECRET,
        'redirect_uri': settings.MICROSOFT_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    tokens = requests.post(token_url, data=data, timeout=10).json()

    access_token = tokens.get('access_token')
    if not access_token:
        return JsonResponse({"error": "Failed to get token"}, status=400)

    user_info = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    ).json()
    email = user_info.get('mail') or user_info.get('userPrincipalName')

    account_data = {
        "user_id": user_id,
        "email_address": email,
        "provider": "outlook",
        "access_token": access_token,
        "refresh_token": tokens.get('refresh_token'),
        "token_expiry": (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(tokens.get('expires_in', 3600)))
        ).isoformat(),
        "inbox_sync_status": "connected",
    }
    upsert_connected_account(account_data)
    syslog("oauth_connect", "microsoft_callback", {"email": email})

    return JsonResponse({"status": "Outlook connected", "email": email})


# ======================
# WEBHOOKS (Gmail + Outlook)
# ======================
@csrf_exempt
def gmail_webhook(request):
    """Handles Gmail push notifications."""
    if request.method == 'GET':
        return JsonResponse({"ok": True})
    try:
        payload = json.loads(request.body)
        email = payload.get('emailAddress')
        history_id = payload.get('historyId')
        if not email:
            return JsonResponse({"error": "no email"}, status=400)
        account = get_account_by_email(email, "gmail")
        if not account:
            return JsonResponse({"error": "not found"}, status=404)
        process_incoming_email.delay(email, "gmail", history_id)
        return JsonResponse({"status": "queued"})
    except Exception as e:
        syslog("webhook_error", "gmail_webhook", {"error": str(e)})
        return JsonResponse({"error": "server error"}, status=500)


@csrf_exempt
def outlook_webhook(request):
    """Handles Outlook webhook validation + events."""
    if request.method == 'GET':
        token = request.GET.get('validationToken')
        if token:
            return HttpResponse(token)
    try:
        for event in json.loads(request.body).get('value', []):
            resource = event.get('resource', '')
            if '/messages' in resource:
                email = resource.split('/')[1]
                process_incoming_email.delay(email, "outlook", None)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        syslog("webhook_error", "outlook_webhook", {"error": str(e)})
        return JsonResponse({"error": "fail"}, status=500)
