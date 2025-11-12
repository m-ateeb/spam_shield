"""
OAuth login views for user authentication
"""
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def google_oauth_login(request):
    """Redirect directly to Google OAuth"""
    request.session['frontend_redirect'] = request.GET.get('redirect', settings.FRONTEND_URL)
    
    from allauth.socialaccount.adapter import get_adapter
    adapter = get_adapter(request)
    app = adapter.get_app(request, 'google')
    
    from django.contrib.sites.shortcuts import get_current_site
    site = get_current_site(request)
    domain = site.domain if ':' in site.domain else f"{site.domain}:8000"
    callback_url = f"{request.scheme}://{domain}/accounts/google/login/callback/"
    
    params = {
        'client_id': app.client_id,
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'prompt': 'select_account',
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return redirect(auth_url)


@require_http_methods(["GET"])
def microsoft_oauth_login(request):
    """Redirect directly to Microsoft OAuth"""
    request.session['frontend_redirect'] = request.GET.get('redirect', settings.FRONTEND_URL)
    
    from allauth.socialaccount.adapter import get_adapter
    adapter = get_adapter(request)
    app = adapter.get_app(request, 'microsoft')
    
    from django.contrib.sites.shortcuts import get_current_site
    site = get_current_site(request)
    domain = site.domain if ':' in site.domain else f"{site.domain}:8000"
    callback_url = f"{request.scheme}://{domain}/accounts/microsoft/login/callback/"
    
    params = {
        'client_id': app.client_id,
        'response_type': 'code',
        'redirect_uri': callback_url,
        'scope': 'User.Read openid profile email',
        'response_mode': 'query',
    }
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
    return redirect(auth_url)

