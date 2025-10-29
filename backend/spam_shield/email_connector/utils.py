# email_connector/utils.py
from django.conf import settings
from jose import jwt
import requests
import re
from bs4 import BeautifulSoup

# ==========================
# JWT UTILITIES
# ==========================

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


# ==========================
# EMAIL PARSING UTILITIES
# ==========================

def extract_sender(raw_msg):
    """
    Extract 'From' or sender email address from a Gmail or Outlook message.
    Works with both Gmail API and Graph API payloads.
    """
    try:
        # Gmail style
        headers = raw_msg.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == "from":
                return h.get("value", "")
        # Outlook style
        if "from" in raw_msg:
            address = raw_msg["from"].get("emailAddress", {}).get("address")
            return address or ""
    except Exception as e:
        print("extract_sender error:", e)
    return ""


def extract_body_html(raw_msg):
    """
    Extract HTML body from Gmail or Outlook message payload.
    Gmail messages often have base64-encoded parts.
    """
    try:
        # Gmail (MIME parts)
        payload = raw_msg.get("payload", {})
        if "body" in payload and payload["body"].get("data"):
            import base64
            data = payload["body"]["data"]
            data += "=" * (-len(data) % 4)  # fix padding
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        # Gmail (multipart)
        for part in payload.get("parts", []):
            mime_type = part.get("mimeType", "")
            if mime_type == "text/html" and part["body"].get("data"):
                import base64
                data = part["body"]["data"]
                data += "=" * (-len(data) % 4)
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        # Outlook fallback
        if "body" in raw_msg:
            return raw_msg["body"].get("content", "")
    except Exception as e:
        print("extract_body_html error:", e)
    return ""


def highlight_urls(html_content):
    """
    Add <mark> highlight tags around URLs found in the email HTML content.
    Helps visually emphasize suspicious links.
    """
    try:
        if not html_content:
            return html_content

        # Regex to find URLs
        url_pattern = r'(https?://[^\s"<]+)'
        highlighted = re.sub(url_pattern, r'<mark style="background-color: yellow">\1</mark>', html_content)
        return highlighted
    except Exception as e:
        print("highlight_urls error:", e)
        return html_content
