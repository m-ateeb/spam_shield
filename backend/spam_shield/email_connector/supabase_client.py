from supabase import create_client, Client
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

fernet = Fernet(settings.FERNET_KEY) if settings.FERNET_KEY else None

def encrypt_token(token: str) -> str:
    if not token or not fernet: return token
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(token_enc: str) -> str:
    if not token_enc or not fernet: return token_enc
    try:
        return fernet.decrypt(token_enc.encode()).decode()
    except InvalidToken:
        logger.error("Invalid token decryption")
        return None

def get_account_by_email(email: str, provider: str):
    res = supabase.table("connected_accounts")\
        .select("*")\
        .eq("email_address", email)\
        .eq("provider", provider)\
        .limit(1)\
        .execute()
    return res.data[0] if res.data else None

def upsert_connected_account(account_data: dict):
    if 'access_token' in account_data:
        account_data['access_token'] = encrypt_token(account_data['access_token'])
    if 'refresh_token' in account_data:
        account_data['refresh_token'] = encrypt_token(account_data['refresh_token'])

    try:
        return supabase.table("connected_accounts").upsert(
            account_data,
            on_conflict="user_id,email_address"
        ).execute()
    except Exception as e:
        logger.error(f"Upsert failed: {e}")
        syslog("db_error", "upsert_connected_account", {"error": str(e), "data": str(account_data)})
        raise

def syslog(event_type: str, task_name: str, payload: dict):
    supabase.table("system_logs").insert({
        "event_type": event_type,
        "task_name": task_name,
        "payload": payload
    }).execute()
