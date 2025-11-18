from bs4 import BeautifulSoup
import re


def extract_display_name(from_header):
    """
    Extract display name from From header.
    Example: "Display Name <email@domain.com>" -> "Display Name"
    """
    import re
    try:
        if not from_header:
            return ""
        
        # Pattern: "Display Name <email@domain.com>"
        match = re.match(r'^(.+?)\s*<[^>]+>$', from_header)
        if match:
            return match.group(1).strip().strip('"')
        
        # If no angle brackets, check if it's just an email
        if '@' in from_header and '<' not in from_header:
            return ""  # Just email, no display name
        
        return from_header.strip()
    except Exception:
        return ""


def extract_sender(raw_msg):
    """
    Extract 'From' or sender email address from a Gmail or Outlook message.
    Works with both Gmail API and Graph API payloads.
    Parses email address from formats like:
    - "Display Name <email@domain.com>"
    - "email@domain.com"
    - "<email@domain.com>"
    Falls back to Return-Path or Reply-To if From header doesn't contain email.
    """
    import re
    try:
        from_header = ""
        headers_list = []
        
        # Gmail style
        headers = raw_msg.get("payload", {}).get("headers", [])
        for h in headers:
            header_name = h.get("name", "").lower()
            header_value = h.get("value", "")
            headers_list.append((header_name, header_value))
            
            if header_name == "from":
                from_header = header_value
        
        # Outlook style
        if not from_header and "from" in raw_msg:
            address = raw_msg["from"].get("emailAddress", {}).get("address")
            if address:
                return address.lower().strip()
        
        if not from_header:
            return ""
        
        # Parse email address from From header
        # Pattern: "Display Name <email@domain.com>" or "email@domain.com"
        # More comprehensive pattern to catch emails in various formats
        email_patterns = [
            r'<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>',  # <email@domain.com>
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',   # email@domain.com (standalone)
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, from_header)
            if match:
                email = match.group(1)
                # Validate it's a proper email
                if '@' in email and '.' in email.split('@')[1]:
                    return email.lower().strip()
        
        # If no email pattern found, check if the entire header is an email
        if '@' in from_header and '.' in from_header.split('@')[-1] if '@' in from_header else '':
            # Might be just an email address
            potential_email = from_header.strip()
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', potential_email):
                return potential_email.lower()
        
        # Fallback: Try Return-Path or Reply-To headers
        for header_name, header_value in headers_list:
            if header_name in ['return-path', 'reply-to'] and header_value:
                for pattern in email_patterns:
                    match = re.search(pattern, header_value)
                    if match:
                        email = match.group(1)
                        if '@' in email and '.' in email.split('@')[1]:
                            return email.lower().strip()
        
        # If no valid email found, return empty (will be filtered out)
        return ""
        
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