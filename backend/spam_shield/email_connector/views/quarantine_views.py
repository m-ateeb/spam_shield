"""
Views for quarantine operations
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from ..services.quarantine_service import QuarantineService

quarantine_service = QuarantineService()


@csrf_exempt
@require_http_methods(["GET"])
def list_quarantined_emails(request):
    """List all quarantined emails"""
    return quarantine_service.list_quarantined_emails(request)


@csrf_exempt
@require_http_methods(["POST"])
def release_quarantined_email(request):
    """Release a quarantined email"""
    try:
        data = json.loads(request.body)
        email_id = data.get('id')
        if not email_id:
            return JsonResponse({'error': 'Email ID required'}, status=400)
        return quarantine_service.release_email(request, email_id)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def delete_quarantined_email(request):
    """Permanently delete a quarantined email"""
    try:
        data = json.loads(request.body)
        email_id = data.get('id')
        if not email_id:
            return JsonResponse({'error': 'Email ID required'}, status=400)
        return quarantine_service.delete_email(request, email_id)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

