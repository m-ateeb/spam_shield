# email_connector/auth_views.py
# Re-export from modular structure for backward compatibility
from .views.auth_oauth_views import google_oauth_login, microsoft_oauth_login
from .views.auth_api_views import (
    get_auth_token,
    email_password_login,
    email_password_signup,
    logout_view,
    user_info,
)

# OAuth callbacks are complex and remain in this file for now
# They can be refactored further if needed
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.conf import settings
from allauth.socialaccount.providers.google.views import oauth2_callback as allauth_google_callback
from allauth.socialaccount.providers.microsoft.views import oauth2_callback as allauth_microsoft_callback
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)


@require_GET
def google_oauth_callback(request):
    """Custom Google OAuth callback - handles both user auth and email account connection."""
    state = request.GET.get('state')
    if state == 'email_account_connection':
        from email_connector.views import google_callback as email_account_callback
        return email_account_callback(request)
    
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', '')
        logger.error(f"OAuth provider error: {error}, description: {error_description}")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason={error}")
    
    try:
        response = allauth_google_callback(request)
        if request.user.is_authenticated:
            token, _ = Token.objects.get_or_create(user=request.user)
            frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
            if 'frontend_redirect' in request.session:
                del request.session['frontend_redirect']
            logger.info(f"OAuth login successful for {request.user.email}")
            return redirect(f"{frontend_url}/login?token={token.key}")
        
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=not_authenticated")
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}", exc_info=True)
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=exception")


@require_GET
def microsoft_oauth_callback(request):
    """Custom Microsoft OAuth callback"""
    state = request.GET.get('state')
    if state == 'email_account_connection':
        from email_connector.views import microsoft_callback as email_account_callback
        return email_account_callback(request)
    
    error = request.GET.get('error')
    if error:
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason={error}")
    
    try:
        response = allauth_microsoft_callback(request)
        if request.user.is_authenticated:
            token, _ = Token.objects.get_or_create(user=request.user)
            frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
            if 'frontend_redirect' in request.session:
                del request.session['frontend_redirect']
            logger.info(f"OAuth login successful for {request.user.email}")
            return redirect(f"{frontend_url}/login?token={token.key}")
        
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=not_authenticated")
    except Exception as e:
        logger.error(f"Error in Microsoft OAuth callback: {e}", exc_info=True)
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=exception")


@require_GET
def oauth_callback(request):
    """Generic OAuth callback router"""
    provider = request.GET.get('provider', 'google')
    if provider == 'microsoft':
        return microsoft_oauth_callback(request)
    return google_oauth_callback(request)

__all__ = [
    'google_oauth_login',
    'microsoft_oauth_login',
    'get_auth_token',
    'email_password_login',
    'email_password_signup',
    'logout_view',
    'user_info',
    'google_oauth_callback',
    'microsoft_oauth_callback',
    'oauth_callback',
]
