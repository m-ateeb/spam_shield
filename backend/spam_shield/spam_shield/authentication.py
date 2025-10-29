import os
import requests
from jose import jwt, JWTError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from spam_shield.settings import supabase  # Import Supabase client from settings

class SupabaseJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        try:
            # Fetch JWKS dynamically (cache in production for performance)
            jwks_url = f"{os.getenv('SUPABASE_URL')}/auth/v1/jwks"
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            # Decode and verify JWT with JWKS (RS256)
            decoded = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience="authenticated",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                }
            )

            # Use 'sub' as identifier (handles no-email users)
            sub = decoded.get('sub')
            if not sub:
                raise AuthenticationFailed('No valid identifier (sub) in token')

            # Fetch user from Supabase (optional for more data)
            user = supabase.auth.get_user(token)
            # Custom logic for no-email: Use sub if email missing
            if not user.user.email:
                print("User authenticated without email; using sub:", sub)

            # Return user object and token for views
            return (user.user, token)
        except JWTError as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except requests.exceptions.RequestException as e:
            raise AuthenticationFailed(f'JWKS fetch failed: {str(e)}')