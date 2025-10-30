# email_connector/views.py
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_http_methods
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests, json, logging

from .supabase_client import (
    upsert_connected_account,
    get_account_by_email,
    syslog,
    decrypt_token,
    supabase,
)
from .auth_utils import require_jwt
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
        f"openid&access_type=offline&prompt=consent"
    )
    return redirect(auth_url)


@require_GET
@require_jwt
def google_callback(request):
    """Handles Google's OAuth callback and redirects to frontend."""
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    # If OAuth error, redirect to frontend with error
    if error:
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error={error}")
    
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=no_code")

    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        tokens = requests.post(token_url, data=data, timeout=10).json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            syslog("oauth_error", "google_callback", {"error": tokens})
            return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=token_failed")

        # Get user info
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

        email = user_info.get("email")
        if not email:
            return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=no_email")

        # Save account
        account_data = {
            "user_id": request.user_id,
            "email_address": email,
            "provider": "gmail",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": (
                datetime.now(timezone.utc)
                + timedelta(seconds=int(tokens.get("expires_in", 3600)))
            ).isoformat(),
            "inbox_sync_status": "connected",
        }
        upsert_connected_account(account_data)
        syslog("oauth_connect", "google_callback", {"email": email})

        # Setup Gmail watch
        try:
            watch_payload = {"topicName": f"projects/{settings.GOOGLE_PROJECT_ID}/topics/gmail-topic"}
            watch_resp = requests.post(
                f"https://gmail.googleapis.com/gmail/v1/users/{email}/watch",
                headers={"Authorization": f"Bearer {access_token}"},
                json=watch_payload,
                timeout=10,
            )
            syslog("gmail_watch", "google_callback", {"status": watch_resp.status_code})
        except Exception as e:
            syslog("gmail_watch_error", "google_callback", {"error": str(e)})

        # Redirect to frontend with success
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_success=gmail")

    except Exception as e:
        syslog("oauth_exception", "google_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=server_error")


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


@require_GET
@require_jwt
def microsoft_callback(request):
    """Handles Microsoft OAuth callback and redirects to frontend."""
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    if error:
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error={error}")
    
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=no_code")

    try:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "code": code,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        tokens = requests.post(token_url, data=data, timeout=10).json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=token_failed")

        user_info = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()
        email = user_info.get("mail") or user_info.get("userPrincipalName")

        account_data = {
            "user_id": request.user_id,
            "email_address": email,
            "provider": "outlook",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": (
                datetime.now(timezone.utc)
                + timedelta(seconds=int(tokens.get("expires_in", 3600)))
            ).isoformat(),
            "inbox_sync_status": "connected",
        }
        upsert_connected_account(account_data)
        syslog("oauth_connect", "microsoft_callback", {"email": email})

        return redirect(f"{settings.FRONTEND_URL}/user?oauth_success=outlook")

    except Exception as e:
        syslog("oauth_exception", "microsoft_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/user?oauth_error=server_error")


# ======================
# WEBHOOKS (Gmail + Outlook)
# ======================
@csrf_exempt
def gmail_webhook(request):
    """Handles Gmail push notifications."""
    if request.method == "GET":
        return JsonResponse({"ok": True})
    try:
        payload = json.loads(request.body)
        email = payload.get("emailAddress")
        history_id = payload.get("historyId")
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
    if request.method == "GET":
        token = request.GET.get("validationToken")
        if token:
            return HttpResponse(token)
    try:
        for event in json.loads(request.body).get("value", []):
            resource = event.get("resource", "")
            if "/messages" in resource:
                email = resource.split("/")[1]
                process_incoming_email.delay(email, "outlook", None)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        syslog("webhook_error", "outlook_webhook", {"error": str(e)})
        return JsonResponse({"error": "fail"}, status=500)


# ======================
# QUARANTINE (Module 5)
# ======================
@require_GET
@require_jwt
def list_quarantined_emails(request):
    """List quarantined emails for logged-in user."""
    res = (
        supabase.table("quarantined_emails")
        .select("id, email_id, reason, status, created_at")
        .eq("user_id", request.user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return JsonResponse({"quarantined": res.data or []}, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def release_quarantined_email(request):
    """Mark quarantined email as released (safe)."""
    try:
        data = json.loads(request.body)
        quarantine_id = data.get("id")
        if not quarantine_id:
            return JsonResponse({"error": "Missing quarantine id"}, status=400)

        supabase.table("quarantined_emails").update({"status": "released"}).eq("id", quarantine_id).execute()
        syslog("quarantine_release", "release_quarantined_email", {"id": quarantine_id})
        return JsonResponse({"status": "released"})
    except Exception as e:
        syslog("quarantine_release_error", "release_quarantined_email", {"error": str(e)})
        return JsonResponse({"error": "failed"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
def delete_quarantined_email(request):
    """Permanently delete quarantined email."""
    try:
        data = json.loads(request.body)
        quarantine_id = data.get("id")
        if not quarantine_id:
            return JsonResponse({"error": "Missing quarantine id"}, status=400)

        supabase.table("quarantined_emails").update({"status": "deleted"}).eq("id", quarantine_id).execute()
        syslog("quarantine_delete", "delete_quarantined_email", {"id": quarantine_id})
        return JsonResponse({"status": "deleted"})
    except Exception as e:
        syslog("quarantine_delete_error", "delete_quarantined_email", {"error": str(e)})
        return JsonResponse({"error": "failed"}, status=500)

def verify_gmail_webhook_signature(request):
    """Verify Gmail push notification signature (optional security layer)."""
    # Gmail doesn't provide signature verification out of the box
    # But you can validate the token from Pub/Sub
    # For now, just check if request comes from Google
    user_agent = request.headers.get('User-Agent', '')
    return 'Google' in user_agent or 'APIs-Google' in user_agent

# UPDATE gmail_webhook function:
@csrf_exempt
def gmail_webhook(request):
    """Handles Gmail push notifications."""
    if request.method == "GET":
        return JsonResponse({"ok": True})
    
    # 🆕 Basic security check
    if not verify_gmail_webhook_signature(request):
        syslog("webhook_unauthorized", "gmail_webhook", {"user_agent": request.headers.get('User-Agent')})
        return JsonResponse({"error": "unauthorized"}, status=401)
    
    try:
        payload = json.loads(request.body)
        email = payload.get("emailAddress")
        history_id = payload.get("historyId")
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
