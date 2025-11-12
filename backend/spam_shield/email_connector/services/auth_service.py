"""
Authentication service
"""
import json
import logging
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def create_user(email: str, password: str, username: str = None) -> tuple[User, bool]:
        """Create a new user"""
        if User.objects.filter(email=email).exists():
            return None, False
        
        username = username or email.split('@')[0]
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return user, True
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        """Authenticate user by email and password"""
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None
    
    @staticmethod
    def get_or_create_token(user: User) -> Token:
        """Get or create API token for user"""
        token, _ = Token.objects.get_or_create(user=user)
        return token
    
    @staticmethod
    def get_user_info(user: User) -> dict:
        """Get user information"""
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }

