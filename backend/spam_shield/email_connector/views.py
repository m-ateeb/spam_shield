# email_connector/views.py
# Re-export from modular structure for backward compatibility
from .views import (
    google_login,
    google_callback,
    microsoft_login,
    microsoft_callback,
    list_quarantined_emails,
    release_quarantined_email,
    delete_quarantined_email,
    gmail_webhook,
    outlook_webhook,
)

__all__ = [
    'google_login',
    'google_callback',
    'microsoft_login',
    'microsoft_callback',
    'list_quarantined_emails',
    'release_quarantined_email',
    'delete_quarantined_email',
    'gmail_webhook',
    'outlook_webhook',
]
