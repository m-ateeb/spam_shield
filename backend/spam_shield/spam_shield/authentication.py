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
            # Try RS256 verification first using JWKS
            jwks_url = f"{os.getenv('SUPABASE_URL')}/auth/v1/jwks"
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            decoded = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience="authenticated",
                options={
                    "verify_signature": True,
                    "verify_exp": True,
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
        except JWTError:
            # Fallback: Some Supabase projects sign tokens with HS256 using JWT secret
            secret = os.getenv('SUPABASE_JWT_SECRET')
            if not secret:
                raise

            try:
                decoded = jwt.decode(
                    token,
                    secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                    }
                )

                sub = decoded.get('sub')
                if not sub:
                    raise AuthenticationFailed('No valid identifier (sub) in token')

                user = supabase.auth.get_user(token)
                if not user.user.email:
                    print("User authenticated without email; using sub:", sub)

                return (user.user, token)
            except JWTError as e:
                raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except requests.exceptions.RequestException as e:
            raise AuthenticationFailed(f'JWKS fetch failed: {str(e)}')