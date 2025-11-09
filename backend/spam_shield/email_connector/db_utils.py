"""
Database utilities using Django ORM - replaces supabase_client functionality
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken
import logging
from .models import (
    ConnectedAccount, Email, EmailAuthResult, URLAnalysis,
    ClassificationResult, QuarantinedEmail, SystemLog
)

logger = logging.getLogger(__name__)

# Fernet encryption for tokens
fernet = Fernet(settings.FERNET_KEY) if settings.FERNET_KEY else None

def encrypt_token(token: str) -> str:
    """Encrypt a token using Fernet."""
    if not token or not fernet:
        return token
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(token_enc: str) -> str:
    """Decrypt a token using Fernet."""
    if not token_enc or not fernet:
        return token_enc
    try:
        return fernet.decrypt(token_enc.encode()).decode()
    except InvalidToken:
        logger.error("Invalid token decryption")
        return None

def get_account_by_email(email: str, provider: str):
    """Get account by email and provider."""
    try:
        account = ConnectedAccount.objects.filter(
            email_address=email,
            provider=provider
        ).first()
        if account:
            # Convert to dict format for compatibility
            return {
                'id': account.id,
                'user_id': str(account.user.id),
                'email_address': account.email_address,
                'provider': account.provider,
                'access_token': account.access_token,
                'refresh_token': account.refresh_token,
                'token_expiry': account.token_expiry.isoformat() if account.token_expiry else None,
                'inbox_sync_status': account.inbox_sync_status,
            }
        return None
    except Exception as e:
        logger.error(f"Error getting account by email: {e}")
        return None

def upsert_connected_account(account_data: dict):
    """Upsert connected account."""
    try:
        user_id = account_data.get('user_id')
        if isinstance(user_id, str):
            user_id = int(user_id)
        
        user = User.objects.get(id=user_id)
        email_address = account_data.get('email_address')
        provider = account_data.get('provider')
        
        # Encrypt tokens
        access_token = account_data.get('access_token', '')
        refresh_token = account_data.get('refresh_token', '')
        
        if access_token:
            access_token = encrypt_token(access_token)
        if refresh_token:
            refresh_token = encrypt_token(refresh_token)
        
        # Parse token_expiry if it's a string
        token_expiry = account_data.get('token_expiry')
        if isinstance(token_expiry, str):
            from dateutil.parser import parse
            token_expiry = parse(token_expiry)
        
        account, created = ConnectedAccount.objects.update_or_create(
            user=user,
            email_address=email_address,
            defaults={
                'provider': provider,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expiry': token_expiry,
                'inbox_sync_status': account_data.get('inbox_sync_status', 'connected'),
            }
        )
        return account
    except Exception as e:
        logger.error(f"Error upserting connected account: {e}")
        raise

def syslog(event_type: str, task_name: str, payload: dict):
    """Log system event."""
    try:
        SystemLog.objects.create(
            event_type=event_type,
            task_name=task_name,
            payload=payload
        )
    except Exception as e:
        logger.error(f"Failed to create system log: {e}")

