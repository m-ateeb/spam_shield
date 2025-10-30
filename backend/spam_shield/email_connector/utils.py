from bs4 import BeautifulSoup
import re


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
    """
    try:
        # Gmail (MIME parts)
        payload = raw_msg.get("payload", {})
        if "body" in payload and payload["body"].get("data"):
            import base64
            data = payload["body"]["data"]
            data += "=" * (-len(data) % 4)
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
    """Add <mark> highlight tags around URLs found in the email HTML content."""
    try:
        if not html_content:
            return html_content
        url_pattern = r'(https?://[^\s"<]+)'
        highlighted = re.sub(url_pattern, r'<mark style="background-color: yellow">\1</mark>', html_content)
        return highlighted
    except Exception as e:
        print("highlight_urls error:", e)
        return html_content