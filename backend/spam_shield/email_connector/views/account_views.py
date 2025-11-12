"""
Account management views
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ..models import ConnectedAccount
from ..auth_utils import require_auth
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def list_connected_accounts(request):
    """List all connected email accounts for logged-in user"""
    try:
        accounts = ConnectedAccount.objects.filter(
            user=request.user
        ).values(
            'id', 'email_address', 'provider', 'inbox_sync_status', 'token_expiry'
        )
        accounts_list = list(accounts)
        logger.info(f"Found {len(accounts_list)} accounts for user {request.user.id}")
        return JsonResponse({"accounts": accounts_list})
    except Exception as e:
        logger.error(f"Error listing accounts: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
@require_auth
def disconnect_account(request):
    """Disconnect/remove a connected email account"""
    try:
        import json
        data = json.loads(request.body)
        account_id = data.get('account_id')
        
        if not account_id:
            return JsonResponse({"error": "account_id required"}, status=400)
        
        account = ConnectedAccount.objects.get(id=account_id, user=request.user)
        account.delete()
        
        logger.info(f"Disconnected account {account_id} for user {request.user.id}")
        return JsonResponse({"success": True})
    except ConnectedAccount.DoesNotExist:
        return JsonResponse({"error": "Account not found"}, status=404)
    except Exception as e:
        logger.error(f"Error disconnecting account: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

