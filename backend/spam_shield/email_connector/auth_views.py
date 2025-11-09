# email_connector/auth_views.py
"""
Views for user authentication using django-allauth
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET
from functools import wraps
import json
import requests
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


def google_oauth_login(request):
    """Redirect directly to Google OAuth, bypassing django-allauth's confirmation page."""
    # Store the frontend URL in session for callback
    request.session['frontend_redirect'] = request.GET.get('redirect', settings.FRONTEND_URL)
    
    # Get the SocialApp from django-allauth to ensure we use correct credentials
    from allauth.socialaccount.adapter import get_adapter
    adapter = get_adapter(request)
    app = adapter.get_app(request, 'google')
    
    # Build the callback URL that django-allauth expects
    from django.contrib.sites.shortcuts import get_current_site
    site = get_current_site(request)
    # Use the site domain, ensuring it includes port if needed
    domain = site.domain if ':' in site.domain else f"{site.domain}:8000"
    callback_url = f"{request.scheme}://{domain}/accounts/google/login/callback/"
    
    # Construct the OAuth URL directly - bypasses confirmation page
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


def microsoft_oauth_login(request):
    """Redirect directly to Microsoft OAuth, bypassing django-allauth's confirmation page."""
    # Store the frontend URL in session for callback
    request.session['frontend_redirect'] = request.GET.get('redirect', settings.FRONTEND_URL)
    
    # Get the SocialApp from django-allauth to ensure we use correct credentials
    from allauth.socialaccount.adapter import get_adapter
    adapter = get_adapter(request)
    app = adapter.get_app(request, 'microsoft')
    
    # Build the callback URL that django-allauth expects
    from django.contrib.sites.shortcuts import get_current_site
    site = get_current_site(request)
    # Use the site domain, ensuring it includes port if needed
    domain = site.domain if ':' in site.domain else f"{site.domain}:8000"
    callback_url = f"{request.scheme}://{domain}/accounts/microsoft/login/callback/"
    
    # Construct the OAuth URL directly - bypasses confirmation page
    params = {
        'client_id': app.client_id,
        'response_type': 'code',
        'redirect_uri': callback_url,
        'scope': 'User.Read openid profile email',
        'response_mode': 'query',
    }
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
    return redirect(auth_url)


@login_required
def get_auth_token(request):
    """Get or create API token for authenticated user."""
    token, created = Token.objects.get_or_create(user=request.user)
    return JsonResponse({
        'token': token.key,
        'user_id': request.user.id,
        'email': request.user.email,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def logout_view(request):
    """Logout endpoint that works with token authentication (no CSRF required)."""
    from django.contrib.auth import logout
    
    # Check if user is authenticated via token
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token_key = None
    if auth_header.startswith('Token ') or auth_header.startswith('Bearer '):
        token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
    
    # If user is authenticated (via session or token), log them out
    user_email = None
    if request.user.is_authenticated:
        user_email = getattr(request.user, 'email', None) or getattr(request.user, 'username', 'unknown')
        # Logout from session (if session-based)
        logout(request)
        logger.info(f"User logged out: {user_email}")
    
    # If token was provided, optionally delete it (frontend will also remove from localStorage)
    # Note: We don't delete the token here to allow graceful logout even if frontend fails
    # Uncomment the next line if you want to invalidate tokens on logout:
    # if token_key:
    #     try:
    #         Token.objects.get(key=token_key).delete()
    #     except Token.DoesNotExist:
    #         pass
    
    # Always return success (idempotent operation)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})


def user_info(request):
    """Get current user information."""
    # Check if user is authenticated via session or token
    if not request.user.is_authenticated:
        # Try to get token from Authorization header
        # Support both 'Token' and 'Bearer' prefixes
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token ') or auth_header.startswith('Bearer '):
            from rest_framework.authtoken.models import Token
            token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
            try:
                token = Token.objects.get(key=token_key)
                # Set user on request for this view
                request.user = token.user
            except Token.DoesNotExist:
                return JsonResponse({'error': 'Invalid token'}, status=401)
        else:
            return JsonResponse({'error': 'Authentication required'}, status=401)
    
    return JsonResponse({
        'id': request.user.id,
        'email': request.user.email,
        'username': request.user.username,
    })


@require_GET
def google_oauth_callback(request):
    """Custom Google OAuth callback - handles both user auth and email account connection."""
    from allauth.socialaccount.providers.google.views import oauth2_callback as allauth_callback
    from allauth.socialaccount.models import SocialAccount
    from django.contrib.auth import login
    from rest_framework.authtoken.models import Token
    
    # Check if this is for email account connection (has state parameter)
    state = request.GET.get('state')
    if state == 'email_account_connection':
        # Route to email account connection callback
        # First, ensure user is authenticated (check session or restore from stored user ID)
        if not request.user.is_authenticated:
            # Try to restore user from session-stored user ID
            user_id = request.session.get('oauth_user_id')
            if user_id:
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=int(user_id))
                    # Restore session
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    logger.info(f"Restored user session for email account OAuth: {user.email} (ID: {user.id})")
                except (User.DoesNotExist, ValueError) as e:
                    logger.error(f"Failed to restore user from session: {e}")
                    frontend_url = settings.FRONTEND_URL
                    return redirect(f"{frontend_url}/settings?oauth_error=session_lost")
            else:
                # No user ID in session - can't proceed
                frontend_url = settings.FRONTEND_URL
                logger.warning("Email account OAuth callback: User not authenticated and no user ID in session")
                return redirect(f"{frontend_url}/settings?oauth_error=session_lost")
        
        # User is authenticated, route to email account connection callback
        logger.info(f"Routing to email account callback for user: {request.user.id}")
        from email_connector.views import google_callback as email_account_callback
        return email_account_callback(request)
    
    # Otherwise, handle as user authentication OAuth
    # Check for OAuth errors from provider
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', '')
        logger.error(f"OAuth provider error: {error}, description: {error_description}")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason={error}")
    
    try:
        # Let django-allauth handle the callback
        # This should process the OAuth code and create/login the user
        response = allauth_callback(request)
        
        # Check if user is authenticated after callback
        if request.user.is_authenticated:
            token, created = Token.objects.get_or_create(user=request.user)
            frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
            if 'frontend_redirect' in request.session:
                del request.session['frontend_redirect']
            logger.info(f"OAuth login successful for {request.user.email}")
            return redirect(f"{frontend_url}/login?token={token.key}")
        
        # If not authenticated, try to find the social account that was just created
        # and manually log the user in
        code = request.GET.get('code')
        if code:
            # Try to find the social account that matches this OAuth flow
            # Get the most recent social account for Google
            try:
                from allauth.socialaccount.models import SocialToken
                # Find social tokens created in the last minute (should be from this callback)
                from django.utils import timezone
                from datetime import timedelta
                recent_tokens = SocialToken.objects.filter(
                    app__provider='google'
                ).filter(
                    account__user__isnull=False
                ).order_by('-id')[:1]
                
                if recent_tokens.exists():
                    social_token = recent_tokens.first()
                    user = social_token.account.user
                    # Manually log the user in
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    token, created = Token.objects.get_or_create(user=user)
                    frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
                    if 'frontend_redirect' in request.session:
                        del request.session['frontend_redirect']
                    logger.info(f"OAuth login successful (manual) for {user.email}")
                    return redirect(f"{frontend_url}/login?token={token.key}")
            except Exception as e:
                logger.error(f"Error in manual login attempt: {e}", exc_info=True)
        
        # If still not authenticated, log the issue
        logger.warning(f"User not authenticated after OAuth callback. Response type: {type(response)}, status: {getattr(response, 'status_code', 'N/A')}")
        if hasattr(response, 'url'):
            logger.warning(f"Response redirect URL: {response.url}")
        if hasattr(response, 'content'):
            logger.warning(f"Response content (first 500 chars): {str(response.content)[:500]}")
        
        # Redirect to frontend with error
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=not_authenticated")
        
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=exception")


@require_GET
def microsoft_oauth_callback(request):
    """Custom Microsoft OAuth callback - properly handle django-allauth flow."""
    from allauth.socialaccount.providers.microsoft.views import oauth2_callback as allauth_callback
    from allauth.socialaccount.models import SocialAccount
    from django.contrib.auth import login
    
    # Check if this is for email account connection (has state parameter)
    state = request.GET.get('state')
    if state == 'email_account_connection':
        # Route to email account connection callback
        # First, ensure user is authenticated (check session or restore from stored user ID)
        if not request.user.is_authenticated:
            # Try to restore user from session-stored user ID
            user_id = request.session.get('oauth_user_id')
            if user_id:
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=int(user_id))
                    # Restore session
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    logger.info(f"Restored user session for Microsoft email account OAuth: {user.email} (ID: {user.id})")
                except (User.DoesNotExist, ValueError) as e:
                    logger.error(f"Failed to restore user from session: {e}")
                    frontend_url = settings.FRONTEND_URL
                    return redirect(f"{frontend_url}/settings?oauth_error=session_lost")
            else:
                # No user ID in session - can't proceed
                frontend_url = settings.FRONTEND_URL
                logger.warning("Microsoft email account OAuth callback: User not authenticated and no user ID in session")
                return redirect(f"{frontend_url}/settings?oauth_error=session_lost")
        
        # User is authenticated, route to email account connection callback
        logger.info(f"Routing to Microsoft email account callback for user: {request.user.id}")
        from email_connector.views import microsoft_callback as email_account_callback
        return email_account_callback(request)
    
    # Otherwise, handle as user authentication OAuth
    # Check for OAuth errors from provider
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', '')
        logger.error(f"OAuth provider error: {error}, description: {error_description}")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason={error}")
    
    try:
        # Let django-allauth handle the callback
        response = allauth_callback(request)
        
        # Check if user is authenticated after callback
        if request.user.is_authenticated:
            token, created = Token.objects.get_or_create(user=request.user)
            frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
            if 'frontend_redirect' in request.session:
                del request.session['frontend_redirect']
            logger.info(f"OAuth login successful for {request.user.email}")
            return redirect(f"{frontend_url}/login?token={token.key}")
        
        # If not authenticated, try to find the social account that was just created
        code = request.GET.get('code')
        if code:
            try:
                from allauth.socialaccount.models import SocialToken
                from django.utils import timezone
                # Find social tokens created recently for Microsoft
                recent_tokens = SocialToken.objects.filter(
                    app__provider='microsoft'
                ).filter(
                    account__user__isnull=False
                ).order_by('-id')[:1]
                
                if recent_tokens.exists():
                    social_token = recent_tokens.first()
                    user = social_token.account.user
                    # Manually log the user in
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    token, created = Token.objects.get_or_create(user=user)
                    frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
                    if 'frontend_redirect' in request.session:
                        del request.session['frontend_redirect']
                    logger.info(f"OAuth login successful (manual) for {user.email}")
                    return redirect(f"{frontend_url}/login?token={token.key}")
            except Exception as e:
                logger.error(f"Error in manual login attempt: {e}", exc_info=True)
        
        # If still not authenticated, log the issue
        logger.warning(f"User not authenticated after OAuth callback. Response type: {type(response)}, status: {getattr(response, 'status_code', 'N/A')}")
        if hasattr(response, 'url'):
            logger.warning(f"Response redirect URL: {response.url}")
        
        # Redirect to frontend with error
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=not_authenticated")
        
    except Exception as e:
        logger.error(f"Error in Microsoft OAuth callback: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed&reason=exception")


def oauth_callback(request):
    """Handle OAuth callback - redirect to frontend with token.
    This is called after django-allauth processes the OAuth callback.
    """
    # Check for OAuth errors in the request (from provider)
    error = request.GET.get('error')
    if error:
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed")
    
    # Check if user is authenticated (django-allauth should have logged them in)
    if not request.user.is_authenticated:
        # If not authenticated, redirect back to login with error
        logger.warning("User not authenticated after OAuth callback")
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed")
    
    # User is authenticated, create/get token and redirect to frontend
    try:
        token, created = Token.objects.get_or_create(user=request.user)
        logger.info(f"OAuth login successful for user: {request.user.email}")
        # Get frontend URL from session or use default
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        if 'frontend_redirect' in request.session:
            del request.session['frontend_redirect']
        return redirect(f"{frontend_url}/login?token={token.key}")
    except Exception as e:
        logger.error(f"Error creating token for OAuth user: {e}", exc_info=True)
        frontend_url = request.session.get('frontend_redirect', settings.FRONTEND_URL)
        return redirect(f"{frontend_url}/login?error=oauth_failed")


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def email_password_login(request):
    """Email/password login endpoint."""
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is None:
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'email': user.email,
            })
        else:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def email_password_signup(request):
    """Email/password signup endpoint."""
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'User with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        # Login user
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

