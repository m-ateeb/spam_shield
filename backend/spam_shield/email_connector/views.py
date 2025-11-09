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

from .db_utils import (
    upsert_connected_account,
    get_account_by_email,
    syslog,
    decrypt_token,
)
from .models import QuarantinedEmail
from .auth_utils import require_auth
from spam_shield.tasks import process_incoming_email

logger = logging.getLogger(__name__)

# ======================
# GOOGLE OAUTH
# ======================
def google_login(request):
    """Redirects user to Google's OAuth consent screen for email account connection."""
    from urllib.parse import urlencode
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import login
    
    # Check authentication - allow session, token auth header, or token query parameter (for extension)
    if not request.user.is_authenticated:
        token_key = None
        
        # Try token from Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token ') or auth_header.startswith('Bearer '):
            token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
        
        # If no header token, try query parameter (for extension use)
        if not token_key:
            token_key = request.GET.get('token')
        
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
                # Create session for OAuth callback
                login(request, token.user, backend='django.contrib.auth.backends.ModelBackend')
                # Store user ID in session for callback (in case session is lost)
                request.session['oauth_user_id'] = str(token.user.id)
                request.session['oauth_provider'] = 'google'
                logger.info(f"Authenticated user via token for OAuth: {token.user.email}")
            except Token.DoesNotExist:
                logger.warning(f"Invalid token provided for OAuth")
                return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
        else:
            logger.warning("No authentication provided for email account OAuth")
            return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
    else:
        # User already authenticated via session - store user ID for callback
        request.session['oauth_user_id'] = str(request.user.id)
        request.session['oauth_provider'] = 'google'
    
    # Build redirect URI - must match what's configured in Google OAuth Console
    # The callback goes to /accounts/google/login/callback/ which is handled by auth_views.google_oauth_callback
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    # Use the backend callback URL that matches the URL routing
    redirect_uri = f"{scheme}://{host}/accounts/google/login/callback/"
    
    # Store the redirect URI in session for use in callback
    request.session['oauth_redirect_uri'] = redirect_uri
    
    # Log the redirect URI being used for debugging
    logger.info(f"Google OAuth - Request host: {host}, Redirect URI: {redirect_uri}, User: {request.user.id}")
    
    # IMPORTANT: The redirect_uri must match EXACTLY what's configured in Google OAuth Console
    # For localhost:8000, add: http://localhost:8000/accounts/google/login/callback/
    # For production, add your production URL with the same path
    
    # Add state parameter to identify this as email account connection OAuth
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': 'email_account_connection',  # Identify this as email account OAuth
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(auth_url)


@require_GET
def google_callback(request):
    """Handles Google's OAuth callback and redirects to frontend."""
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    
    # Restore user authentication if lost
    if not request.user.is_authenticated:
        user_id = request.session.get('oauth_user_id')
        if user_id:
            try:
                user = User.objects.get(id=int(user_id))
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.user_id = str(user.id)
                logger.info(f"Restored user session in google_callback: {user.email}")
            except (User.DoesNotExist, ValueError) as e:
                logger.error(f"Failed to restore user from session in google_callback: {e}")
                return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
        else:
            logger.warning("google_callback: User not authenticated and no user ID in session")
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
    else:
        request.user_id = str(request.user.id)
    
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    # If OAuth error, redirect to frontend with error
    if error:
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error={error}")
    
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=no_code")

    try:
        # Get the redirect URI from session (should match what was sent to Google)
        redirect_uri = request.session.get('oauth_redirect_uri')
        if not redirect_uri:
            # Fallback to building from request
            host = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
            redirect_uri = f"{scheme}://{host}/accounts/google/login/callback/"
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        tokens = requests.post(token_url, data=data, timeout=10).json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            syslog("oauth_error", "google_callback", {"error": tokens})
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=token_failed")

        # Get user info
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

        email = user_info.get("email")
        if not email:
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=no_email")

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
        try:
            account = upsert_connected_account(account_data)
            logger.info(f"Successfully saved/updated account: {email} for user {request.user_id}")
            syslog("oauth_connect", "google_callback", {"email": email, "user_id": request.user_id, "account_id": account.id})
        except Exception as e:
            logger.error(f"Failed to save account: {e}", exc_info=True)
            syslog("oauth_error", "google_callback", {"error": str(e), "email": email})
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=save_failed")

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

        # Clean up session data
        if 'oauth_user_id' in request.session:
            del request.session['oauth_user_id']
        if 'oauth_provider' in request.session:
            del request.session['oauth_provider']
        if 'oauth_redirect_uri' in request.session:
            del request.session['oauth_redirect_uri']
        
        # Redirect to frontend settings page with success
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_success=gmail")

    except Exception as e:
        syslog("oauth_exception", "google_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=server_error")


# ======================
# MICROSOFT OAUTH
# ======================
def microsoft_login(request):
    """Redirects to Microsoft OAuth screen."""
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import login
    
    # Check authentication - allow session, token auth header, or token query parameter (for extension)
    if not request.user.is_authenticated:
        token_key = None
        
        # Try token from Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token ') or auth_header.startswith('Bearer '):
            token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
        
        # If no header token, try query parameter (for extension use)
        if not token_key:
            token_key = request.GET.get('token')
        
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
                # Create session for OAuth callback
                login(request, token.user, backend='django.contrib.auth.backends.ModelBackend')
                # Store user ID in session for callback (in case session is lost)
                request.session['oauth_user_id'] = str(token.user.id)
                request.session['oauth_provider'] = 'microsoft'
                logger.info(f"Authenticated user via token for Microsoft OAuth: {token.user.email}")
            except Token.DoesNotExist:
                logger.warning(f"Invalid token provided for Microsoft OAuth")
                return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
        else:
            logger.warning("No authentication provided for Microsoft email account OAuth")
            return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
    else:
        # User already authenticated via session - store user ID for callback
        request.session['oauth_user_id'] = str(request.user.id)
        request.session['oauth_provider'] = 'microsoft'
    
    # Build redirect URI - must match what's configured in Microsoft Azure Portal
    host = request.get_host()
    scheme = 'https' if request.is_secure() else 'http'
    redirect_uri = f"{scheme}://{host}/accounts/microsoft/login/callback/"
    
    # Store the redirect URI in session for use in callback
    request.session['oauth_redirect_uri'] = redirect_uri
    
    from urllib.parse import urlencode
    params = {
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'User.Read Mail.Read Mail.ReadWrite offline_access openid profile email',
        'response_mode': 'query',
        'state': 'email_account_connection',  # Identify this as email account OAuth
    }
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
    return redirect(auth_url)


@require_GET
def microsoft_callback(request):
    """Handles Microsoft OAuth callback and redirects to frontend."""
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    
    # Restore user authentication if lost
    if not request.user.is_authenticated:
        user_id = request.session.get('oauth_user_id')
        if user_id:
            try:
                user = User.objects.get(id=int(user_id))
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.user_id = str(user.id)
                logger.info(f"Restored user session in microsoft_callback: {user.email}")
            except (User.DoesNotExist, ValueError) as e:
                logger.error(f"Failed to restore user from session in microsoft_callback: {e}")
                return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
        else:
            logger.warning("microsoft_callback: User not authenticated and no user ID in session")
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
    else:
        request.user_id = str(request.user.id)
    
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    if error:
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error={error}")
    
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=no_code")

    try:
        # Get the redirect URI from session (should match what was sent to Microsoft)
        redirect_uri = request.session.get('oauth_redirect_uri')
        if not redirect_uri:
            # Fallback to building from request
            host = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
            redirect_uri = f"{scheme}://{host}/accounts/microsoft/login/callback/"
        
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "code": code,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        tokens = requests.post(token_url, data=data, timeout=10).json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=token_failed")

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

        # Clean up session data
        if 'oauth_user_id' in request.session:
            del request.session['oauth_user_id']
        if 'oauth_provider' in request.session:
            del request.session['oauth_provider']
        if 'oauth_redirect_uri' in request.session:
            del request.session['oauth_redirect_uri']
        
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_success=outlook")

    except Exception as e:
        syslog("oauth_exception", "microsoft_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=server_error")


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
@require_auth
def list_quarantined_emails(request):
    """List quarantined emails for logged-in user."""
    try:
        user = request.user
        quarantined = QuarantinedEmail.objects.filter(
            user=user
        ).select_related('email', 'email__classification').order_by('-created_at')
        
        result = []
        for q in quarantined:
            email = q.email
            classification = getattr(email, 'classification', None)
            
            # Get threat type from classification or reason
            threat = 'Unknown'
            score = 0
            if classification:
                if classification.rule_engine_verdict == 'malicious':
                    threat = 'Malicious'
                elif 'phishing' in q.reason.lower():
                    threat = 'Phishing'
                elif 'spam' in q.reason.lower():
                    threat = 'Spam'
                elif 'malware' in q.reason.lower():
                    threat = 'Malware'
                score = int(classification.confidence_score) if classification.confidence_score else 0
            
            result.append({
                'id': q.id,
                'email_id': email.id,
                'sender': email.sender,
                'subject': email.subject,
                'date': q.created_at.strftime('%Y-%m-%d %H:%M') if q.created_at else '',
                'threat': threat,
                'score': score,
                'reason': q.reason,
                'status': q.status,
                'created_at': q.created_at.isoformat() if q.created_at else None,
            })
        
        return JsonResponse({"quarantined": result}, safe=False)
    except Exception as e:
        logger.error(f"Error listing quarantined emails: {e}", exc_info=True)
        return JsonResponse({"quarantined": []}, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def release_quarantined_email(request):
    """Mark quarantined email as released (safe)."""
    try:
        data = json.loads(request.body)
        quarantine_id = data.get("id")
        if not quarantine_id:
            return JsonResponse({"error": "Missing quarantine id"}, status=400)

        QuarantinedEmail.objects.filter(id=quarantine_id, user=request.user).update(status="released")
        syslog("quarantine_release", "release_quarantined_email", {"id": quarantine_id})
        return JsonResponse({"status": "released"})
    except Exception as e:
        syslog("quarantine_release_error", "release_quarantined_email", {"error": str(e)})
        return JsonResponse({"error": "failed"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def delete_quarantined_email(request):
    """Permanently delete quarantined email."""
    try:
        data = json.loads(request.body)
        quarantine_id = data.get("id")
        if not quarantine_id:
            return JsonResponse({"error": "Missing quarantine id"}, status=400)

        QuarantinedEmail.objects.filter(id=quarantine_id, user=request.user).update(status="deleted")
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
