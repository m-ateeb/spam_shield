"""
OAuth service for handling authentication flows
"""
import logging
from urllib.parse import urlencode
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from django.contrib.auth.models import User
import requests

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for OAuth authentication flows"""
    
    @staticmethod
    def authenticate_user(request):
        """Authenticate user from token or session"""
        if request.user.is_authenticated:
            return request.user
        
        token_key = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token ') or auth_header.startswith('Bearer '):
            token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
        
        if not token_key:
            token_key = request.GET.get('token')
        
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
                login(request, token.user, backend='django.contrib.auth.backends.ModelBackend')
                request.session['oauth_user_id'] = str(token.user.id)
                logger.info(f"Authenticated user via token: {token.user.email}")
                return token.user
            except Token.DoesNotExist:
                logger.warning("Invalid token provided for OAuth")
                return None
        
        return None
    
    @staticmethod
    def build_redirect_uri(request, path):
        """Build OAuth redirect URI"""
        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        return f"{scheme}://{host}{path}"
    
    @staticmethod
    def get_google_auth_url(redirect_uri):
        """Build Google OAuth URL"""
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': 'email_account_connection',
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    @staticmethod
    def get_microsoft_auth_url(redirect_uri):
        """Build Microsoft OAuth URL"""
        params = {
            'client_id': settings.MICROSOFT_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': 'User.Read Mail.Read Mail.ReadWrite offline_access openid profile email',
            'response_mode': 'query',
            'state': 'email_account_connection',
        }
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
    
    @staticmethod
    def exchange_google_code(code, redirect_uri):
        """Exchange Google OAuth code for tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        return requests.post(token_url, data=data, timeout=10).json()
    
    @staticmethod
    def exchange_microsoft_code(code, redirect_uri):
        """Exchange Microsoft OAuth code for tokens"""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "code": code,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        return requests.post(token_url, data=data, timeout=10).json()
    
    @staticmethod
    def get_google_user_info(access_token):
        """Get Google user info"""
        return requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()
    
    @staticmethod
    def get_microsoft_user_info(access_token):
        """Get Microsoft user info"""
        return requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

