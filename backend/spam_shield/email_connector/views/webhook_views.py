"""
Webhook views for Gmail and Outlook push notifications
"""
import hmac
import hashlib
import json
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
    """Handle Gmail push notifications"""
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
            message_id = data['message'].get('data')
            if message_id:
                # Decode base64 message ID if needed
                import base64
                decoded = base64.b64decode(message_id).decode('utf-8')
                logger.info(f"Gmail webhook received for message: {decoded}")
                # Queue email processing
                process_incoming_email.delay(decoded, 'gmail')
        
        return JsonResponse({'status': 'ok'})
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

