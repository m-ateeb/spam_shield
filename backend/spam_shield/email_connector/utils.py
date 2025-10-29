# email_connector/utils.py
from django.conf import settings
from jose import jwt
import requests

def extract_jwt(request):
    """Extract the Supabase JWT token from Authorization header"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None


def get_user_id_from_jwt(token: str):
    """Decode Supabase JWT and extract user_id (sub)"""
    try:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
        jwks = requests.get(jwks_url).json()
        payload = jwt.decode(token, jwks, algorithms=["RS256"], audience="authenticated")
        return payload.get("sub")
    except Exception as e:
        print("JWT decode failed:", e)
        return None
