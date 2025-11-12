"""
Dashboard API views
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from ..auth_utils import require_auth
from ..services.dashboard_service import DashboardService

dashboard_service = DashboardService()


@csrf_exempt
@require_GET
@require_auth
def dashboard_summary(request):
    """Get user dashboard summary"""
    try:
        summary = dashboard_service.get_user_summary(request.user)
        return JsonResponse(summary)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_GET
@require_auth
def admin_dashboard_summary(request):
    """Get admin dashboard summary"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    try:
        summary = dashboard_service.get_admin_summary()
        return JsonResponse(summary)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_GET
@require_auth
def check_admin(request):
    """Check if user is admin"""
    return JsonResponse({
        'is_admin': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
    })

