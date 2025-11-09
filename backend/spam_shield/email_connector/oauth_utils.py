import requests
from datetime import datetime, timezone, timedelta
from django.conf import settings
from email_connector.db_utils import decrypt_token, encrypt_token, syslog
from email_connector.models import ConnectedAccount, Email


def refresh_google_access_token(refresh_token: str) -> dict:
    """Refresh Google OAuth token when expired."""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(token_url, data=data, timeout=10)
        resp.raise_for_status()
        tokens = resp.json()
        return {
            "access_token": tokens.get("access_token"),
            "expires_in": tokens.get("expires_in", 3600),
        }
    except Exception as e:
        syslog("token_refresh_error", "refresh_google_access_token", {"error": str(e)})
        return None


def refresh_microsoft_access_token(refresh_token: str) -> dict:
    """Refresh Microsoft OAuth token when expired."""
    try:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "User.Read Mail.Read Mail.ReadWrite offline_access",
        }
        resp = requests.post(token_url, data=data, timeout=10)
        resp.raise_for_status()
        tokens = resp.json()
        return {
            "access_token": tokens.get("access_token"),
            "expires_in": tokens.get("expires_in", 3600),
        }
    except Exception as e:
        syslog("token_refresh_error", "refresh_microsoft_access_token", {"error": str(e)})
        return None


def get_valid_access_token(account) -> str:
    """
    Get valid access token, refreshing if needed.
    Accepts ConnectedAccount model instance or dict for backward compatibility.
    Returns decrypted access token or None if refresh fails.
    """
    # Handle both model instance and dict
    if hasattr(account, 'token_expiry'):
        token_expiry = account.token_expiry
        access_token = account.access_token
        refresh_token = account.refresh_token
        provider = account.provider
        account_id = account.id
    else:
        # Dict format (backward compatibility)
        token_expiry = account.get("token_expiry")
        access_token = account.get("access_token")
        refresh_token = account.get("refresh_token")
        provider = account.get("provider")
        account_id = account.get("id")
    
    if not token_expiry:
        return decrypt_token(access_token)

    # Handle string datetime
    if isinstance(token_expiry, str):
        expiry_time = datetime.fromisoformat(token_expiry.replace("Z", "+00:00"))
    else:
        expiry_time = token_expiry
    
    now = datetime.now(timezone.utc)

    # Refresh if token expires in next 5 minutes
    if expiry_time <= now + timedelta(minutes=5):
        decrypted_refresh = decrypt_token(refresh_token) if refresh_token else None
        if not decrypted_refresh:
            syslog("no_refresh_token", "get_valid_access_token", {"account_id": account_id})
            return None

        # Refresh based on provider
        if provider == "gmail":
            new_tokens = refresh_google_access_token(refresh_token)
        elif provider == "outlook":
            new_tokens = refresh_microsoft_access_token(refresh_token)
        else:
            return None

        if not new_tokens:
            return None

        # Update account with new token
        new_expiry = datetime.now(timezone.utc) + timedelta(seconds=new_tokens["expires_in"])
        account.access_token = encrypt_token(new_tokens["access_token"])
        account.token_expiry = new_expiry
        account.save()

        return new_tokens["access_token"]

    return decrypt_token(account.access_token)


# ==========================================
# EMAIL ACTION EXECUTION (FR05-05)
# ==========================================

def apply_gmail_action(message_id: str, action: str, email_address: str, token: str) -> bool:
    """
    Apply spam/delete action to Gmail message.
    Actions: 'spam', 'delete', 'allow'
    """
    try:
        url = f"https://gmail.googleapis.com/gmail/v1/users/{email_address}/messages/{message_id}/modify"
        headers = {"Authorization": f"Bearer {token}"}

        if action == "spam":
            body = {"addLabelIds": ["SPAM"]}
        elif action == "delete":
            body = {"addLabelIds": ["TRASH"]}
        elif action == "allow":
            body = {"removeLabelIds": ["SPAM"]}
        else:
            return False

        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        syslog("gmail_action_applied", "apply_gmail_action", {
            "message_id": message_id, "action": action
        })
        return True

    except Exception as e:
        syslog("gmail_action_error", "apply_gmail_action", {
            "message_id": message_id, "action": action, "error": str(e)
        })
        return False


def apply_outlook_action(message_id: str, action: str, token: str) -> bool:
    """
    Apply spam/delete action to Outlook message.
    Actions: 'spam', 'delete', 'allow'
    """
    try:
        if action == "spam":
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            body = {"destinationId": "junkemail"}
            resp = requests.post(url, headers=headers, json=body, timeout=10)

        elif action == "delete":
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.delete(url, headers=headers, timeout=10)

        elif action == "allow":
            url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/move"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            body = {"destinationId": "inbox"}
            resp = requests.post(url, headers=headers, json=body, timeout=10)

        else:
            return False

        resp.raise_for_status()
        syslog("outlook_action_applied", "apply_outlook_action", {
            "message_id": message_id, "action": action
        })
        return True

    except Exception as e:
        syslog("outlook_action_error", "apply_outlook_action", {
            "message_id": message_id, "action": action, "error": str(e)
        })
        return False


def execute_email_action(email_id: int, action: str):
    """
    Execute the final action on an email (spam/delete/allow).
    Called after classification in decision_engine.py
    Note: "quarantine" action is converted to "spam" for Gmail/Outlook APIs
    """
    try:
        try:
            email_obj = Email.objects.get(id=email_id)
        except Email.DoesNotExist:
            syslog("execute_action_error", "execute_email_action", {"email_id": email_id, "error": "Email not found"})
            return False

        message_id = email_obj.message_id
        account = email_obj.account
        token = get_valid_access_token(account)
        if not token:
            syslog("execute_action_error", "execute_email_action", {"email_id": email_id, "error": "No valid token"})
            return False

        # Convert "quarantine" to "spam" for API calls
        api_action = "spam" if action == "quarantine" else action

        if account.provider == "gmail":
            result = apply_gmail_action(message_id, api_action, account.email_address, token)
            syslog("execute_action_result", "execute_email_action", {
                "email_id": email_id,
                "action": action,
                "api_action": api_action,
                "provider": "gmail",
                "success": result
            })
            return result
        elif account.provider == "outlook":
            result = apply_outlook_action(message_id, api_action, token)
            syslog("execute_action_result", "execute_email_action", {
                "email_id": email_id,
                "action": action,
                "api_action": api_action,
                "provider": "outlook",
                "success": result
            })
            return result

        return False

    except Exception as e:
        syslog("execute_action_error", "execute_email_action", {"email_id": email_id, "error": str(e)})
        return False