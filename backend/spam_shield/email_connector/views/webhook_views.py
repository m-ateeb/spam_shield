"""
Webhook views for Gmail and Outlook push notifications
"""
import hmac
import hashlib
import json
import base64
import binascii
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

from spam_shield.tasks import process_incoming_email

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def gmail_webhook(request):
    """
    Handle Gmail push notifications from Google Pub/Sub.
    
    Gmail push notifications come in the format:
    {
        "message": {
            "data": "<base64_encoded_json>",
            "messageId": "...",
            "publishTime": "..."
        }
    }
    
    The decoded data contains:
    {
        "emailAddress": "user@example.com",
        "historyId": "12345"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Verify webhook signature if configured
        if hasattr(settings, 'GMAIL_WEBHOOK_SECRET'):
            signature = request.META.get('HTTP_X_GOOGLE_SIGNATURE', '')
            if not verify_gmail_signature(request.body, signature):
                logger.warning("Invalid Gmail webhook signature")
                return HttpResponse(status=401)
        
        # Process the notification
        if 'message' in data:
            encoded_data = data['message'].get('data')
            if encoded_data:
                try:
                    # Decode base64 data
                    decoded_bytes = base64.b64decode(encoded_data)
                    notification_data = json.loads(decoded_bytes.decode('utf-8'))
                    
                    email_address = notification_data.get('emailAddress')
                    history_id = notification_data.get('historyId')
                    
                    if email_address and history_id:
                        logger.info(f"Gmail webhook received: email={email_address}, historyId={history_id}")
                        # Queue email processing with history_id for incremental updates
                        process_incoming_email.delay(email_address, 'gmail', history_id=history_id)
                    else:
                        logger.warning(f"Gmail webhook missing required fields: {notification_data}")
                except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Error decoding Gmail webhook data: {e}")
                    return JsonResponse({'error': 'Invalid message data'}, status=400)
        
        return JsonResponse({'status': 'ok'})
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Gmail webhook: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def outlook_webhook(request):
    """Handle Outlook push notifications"""
    try:
        data = json.loads(request.body)
        
        # Process notifications
        if 'value' in data:
            for notification in data['value']:
                resource = notification.get('resource')
                if resource:
                    logger.info(f"Outlook webhook received for resource: {resource}")
                    # Queue email processing
                    process_incoming_email.delay(resource, 'outlook')
        
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error processing Outlook webhook: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def verify_gmail_signature(payload, signature):
    """Verify Gmail webhook signature"""
    if not hasattr(settings, 'GMAIL_WEBHOOK_SECRET'):
        return True  # Skip verification if secret not configured
    
    expected = hmac.new(
        settings.GMAIL_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

