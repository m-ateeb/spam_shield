"""
OAuth views for Google and Microsoft email account connections
"""
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.conf import settings
from datetime import datetime, timedelta, timezone
import logging

from ..services.oauth_service import OAuthService
from ..db_utils import upsert_connected_account, syslog

logger = logging.getLogger(__name__)
oauth_service = OAuthService()


@require_GET
def google_login(request):
    """Redirects user to Google's OAuth consent screen"""
    user = oauth_service.authenticate_user(request)
    if not user:
        return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
    
    request.session['oauth_provider'] = 'google'
    redirect_uri = oauth_service.build_redirect_uri(request, '/accounts/google/login/callback/')
    request.session['oauth_redirect_uri'] = redirect_uri
    
    logger.info(f"Google OAuth - User: {user.id}, Redirect URI: {redirect_uri}")
    auth_url = oauth_service.get_google_auth_url(redirect_uri)
    return redirect(auth_url)


@require_GET
def google_callback(request):
    """Handles Google's OAuth callback"""
    from django.contrib.auth.models import User
    from django.contrib.auth import login
    
    if not request.user.is_authenticated:
        user_id = request.session.get('oauth_user_id')
        if user_id:
            try:
                user = User.objects.get(id=int(user_id))
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.user_id = str(user.id)
            except (User.DoesNotExist, ValueError):
                return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
        else:
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
        redirect_uri = request.session.get('oauth_redirect_uri')
        if not redirect_uri:
            redirect_uri = oauth_service.build_redirect_uri(request, '/accounts/google/login/callback/')
        
        tokens = oauth_service.exchange_google_code(code, redirect_uri)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            syslog("oauth_error", "google_callback", {"error": tokens})
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=token_failed")

        user_info = oauth_service.get_google_user_info(access_token)
        email = user_info.get("email")
        if not email:
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=no_email")

        account_data = {
            "user_id": request.user_id,
            "email_address": email,
            "provider": "gmail",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": (
                datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
            ).isoformat(),
            "inbox_sync_status": "connected",
        }
        
        account = upsert_connected_account(account_data)
        logger.info(f"Successfully saved account: {email} for user {request.user_id}")
        syslog("oauth_connect", "google_callback", {"email": email, "user_id": request.user_id})
        
        # Setup Gmail watch for push notifications
        try:
            import requests
            watch_payload = {"topicName": f"projects/{settings.GOOGLE_PROJECT_ID}/topics/gmail-topic"}
            watch_response = requests.post(
                f"https://gmail.googleapis.com/gmail/v1/users/{email}/watch",
                headers={"Authorization": f"Bearer {access_token}"},
                json=watch_payload,
                timeout=10,
            )
            if watch_response.status_code == 200:
                watch_data = watch_response.json()
                logger.info(f"Gmail watch setup successful for {email}, expiration: {watch_data.get('expiration')}")
                syslog("gmail_watch_success", "google_callback", {
                    "email": email,
                    "expiration": watch_data.get("expiration")
                })
            else:
                logger.warning(f"Gmail watch setup failed: {watch_response.status_code} - {watch_response.text}")
                syslog("gmail_watch_error", "google_callback", {
                    "error": f"HTTP {watch_response.status_code}: {watch_response.text}"
                })
        except Exception as e:
            logger.error(f"Error setting up Gmail watch: {e}", exc_info=True)
            syslog("gmail_watch_error", "google_callback", {"error": str(e)})
        
        # Trigger initial scan of 50 most recent emails
        try:
            from spam_shield.tasks import scan_initial_emails
            scan_initial_emails.delay(account.id)
            logger.info(f"Triggered initial email scan for account {account.id} ({email})")
            syslog("initial_scan_triggered", "google_callback", {
                "email": email,
                "account_id": account.id
            })
        except Exception as e:
            logger.error(f"Error triggering initial email scan: {e}", exc_info=True)
            syslog("initial_scan_trigger_error", "google_callback", {"error": str(e)})

        # Clean up session
        for key in ['oauth_user_id', 'oauth_provider', 'oauth_redirect_uri']:
            request.session.pop(key, None)
        
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_success=gmail")
    except Exception as e:
        syslog("oauth_exception", "google_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=server_error")


@require_GET
def microsoft_login(request):
    """Redirects to Microsoft OAuth screen"""
    user = oauth_service.authenticate_user(request)
    if not user:
        return redirect(f"{settings.FRONTEND_URL}/login?error=email_oauth_requires_login")
    
    request.session['oauth_provider'] = 'microsoft'
    redirect_uri = oauth_service.build_redirect_uri(request, '/accounts/microsoft/login/callback/')
    request.session['oauth_redirect_uri'] = redirect_uri
    
    auth_url = oauth_service.get_microsoft_auth_url(redirect_uri)
    return redirect(auth_url)


@require_GET
def microsoft_callback(request):
    """Handles Microsoft OAuth callback"""
    from django.contrib.auth.models import User
    from django.contrib.auth import login
    
    if not request.user.is_authenticated:
        user_id = request.session.get('oauth_user_id')
        if user_id:
            try:
                user = User.objects.get(id=int(user_id))
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.user_id = str(user.id)
            except (User.DoesNotExist, ValueError):
                return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=session_lost")
        else:
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
        redirect_uri = request.session.get('oauth_redirect_uri')
        if not redirect_uri:
            redirect_uri = oauth_service.build_redirect_uri(request, '/accounts/microsoft/login/callback/')
        
        tokens = oauth_service.exchange_microsoft_code(code, redirect_uri)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=token_failed")

        user_info = oauth_service.get_microsoft_user_info(access_token)
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        if not email:
            return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=no_email")

        account_data = {
            "user_id": request.user_id,
            "email_address": email,
            "provider": "outlook",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": (
                datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
            ).isoformat(),
            "inbox_sync_status": "connected",
        }
        
        account = upsert_connected_account(account_data)
        logger.info(f"Successfully saved account: {email} for user {request.user_id}")
        syslog("oauth_connect", "microsoft_callback", {"email": email, "user_id": request.user_id})

        # Clean up session
        for key in ['oauth_user_id', 'oauth_provider', 'oauth_redirect_uri']:
            request.session.pop(key, None)
        
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_success=outlook")
    except Exception as e:
        syslog("oauth_exception", "microsoft_callback", {"error": str(e)})
        return redirect(f"{settings.FRONTEND_URL}/settings?oauth_error=server_error")

