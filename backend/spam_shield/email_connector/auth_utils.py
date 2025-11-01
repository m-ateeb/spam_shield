from django.http import JsonResponse
from django.conf import settings
from functools import wraps
from jose import jwt, JWTError
import requests
import os


def extract_jwt(request):
    """Extract JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None


def get_user_id_from_jwt(token: str):
    """Decode Supabase JWT and extract user_id.

    Tries RS256 via JWKS first; falls back to HS256 using SUPABASE_JWT_SECRET if provided.
    """
    # First try RS256 with JWKS
    try:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
        jwks = requests.get(jwks_url).json()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="authenticated",
            options={
                "verify_signature": True,
                "verify_exp": True,
            }
        )
        return payload.get("sub")
    except JWTError:
        # Fallback to HS256 if project uses symmetric signing
        secret = getattr(settings, 'SUPABASE_JWT_SECRET', None) or os.getenv('SUPABASE_JWT_SECRET')
        if not secret:
            return None
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                }
            )
            return payload.get("sub")
        except Exception as e:
            print("JWT decode failed:", e)
            return None
    except Exception as e:
        print("JWT decode failed:", e)
        return None


def require_jwt(view_func):
    """Decorator for JWT-protected endpoints."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        jwt_token = extract_jwt(request)
        if not jwt_token:
            return JsonResponse({"error": "No JWT provided"}, status=401)
        user_id = get_user_id_from_jwt(jwt_token)
        if not user_id:
            return JsonResponse({"error": "Invalid or expired JWT"}, status=401)
        request.user_id = user_id
        return view_func(request, *args, **kwargs)
    return wrapper