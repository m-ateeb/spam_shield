from .oauth_views import google_login, google_callback, microsoft_login, microsoft_callback
from .quarantine_views import list_quarantined_emails, release_quarantined_email, delete_quarantined_email
from .webhook_views import gmail_webhook, outlook_webhook

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

