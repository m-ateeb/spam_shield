from django.http import JsonResponse
from django.contrib.auth.models import User
from functools import wraps
from rest_framework.authtoken.models import Token


def require_auth(view_func):
    """Decorator for authenticated endpoints using Django user (supports both session and token auth)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # First check if user is authenticated via session
        if request.user and request.user.is_authenticated:
            request.user_id = str(request.user.id)
            return view_func(request, *args, **kwargs)
        
        # If not session auth, try token authentication
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header:
            # Support both 'Token' and 'Bearer' prefixes
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
            elif auth_header.startswith('Bearer '):
                token_key = auth_header.split(' ', 1)[1] if ' ' in auth_header else ''
            else:
                token_key = None
            
            if token_key:
                try:
                    token = Token.objects.get(key=token_key)
                    request.user = token.user
                    request.user_id = str(token.user.id)
                    return view_func(request, *args, **kwargs)
                except Token.DoesNotExist:
                    pass
        
        # No valid authentication found
        return JsonResponse({"error": "Authentication required"}, status=401)
    return wrapper