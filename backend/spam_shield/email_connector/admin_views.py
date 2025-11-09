# email_connector/admin_views.py
"""
Admin-specific API endpoints
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from email_connector.auth_utils import require_auth
from email_connector.models import Email, ClassificationResult, QuarantinedEmail, ConnectedAccount

logger = logging.getLogger(__name__)


@require_GET
@require_auth
def admin_users_list(request):
    """List all users with their stats - admin only."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        users = User.objects.all().order_by('-date_joined')
        users_list = []
        
        for user in users:
            # Get user stats
            total_emails = Email.objects.filter(user=user).count()
            safe_emails = ClassificationResult.objects.filter(
                email__user=user,
                rule_engine_verdict='safe'
            ).count()
            malicious_emails = ClassificationResult.objects.filter(
                email__user=user,
                rule_engine_verdict__in=['malicious', 'phishing']
            ).count()
            quarantined = QuarantinedEmail.objects.filter(user=user, status='pending').count()
            connected_accounts = ConnectedAccount.objects.filter(user=user).count()
            
            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'stats': {
                    'total_emails': total_emails,
                    'safe_emails': safe_emails,
                    'malicious_emails': malicious_emails,
                    'quarantined': quarantined,
                    'connected_accounts': connected_accounts,
                }
            })
        
        return JsonResponse({"users": users_list})
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "PUT"])
@require_auth
def admin_user_update(request):
    """Update user status (activate/deactivate, make admin, etc.) - admin only."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=400)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        
        # Prevent self-modification of superuser status
        if user.id == request.user.id and 'is_superuser' in data:
            return JsonResponse({"error": "Cannot modify your own superuser status"}, status=400)
        
        # Update fields
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_staff' in data:
            user.is_staff = data['is_staff']
        if 'is_superuser' in data:
            user.is_superuser = data['is_superuser']
        
        user.save()
        
        logger.info(f"User {user.id} updated by admin {request.user.id}")
        return JsonResponse({"success": True, "message": f"User {user.username} updated successfully"})
    except Exception as e:
        logger.error(f"Error updating user: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
@require_auth
def admin_reports_summary(request):
    """Get comprehensive admin reports - admin only."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        # Overall stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_emails = Email.objects.count()
        
        # Classification stats
        total_classified = ClassificationResult.objects.count()
        safe_count = ClassificationResult.objects.filter(rule_engine_verdict='safe').count()
        suspicious_count = ClassificationResult.objects.filter(rule_engine_verdict='suspicious').count()
        phishing_count = ClassificationResult.objects.filter(rule_engine_verdict__in=['malicious', 'phishing']).count()
        
        # Recent activity
        emails_last_7_days = Email.objects.filter(received_at__gte=last_7_days).count()
        emails_last_30_days = Email.objects.filter(received_at__gte=last_30_days).count()
        
        quarantined_last_7_days = QuarantinedEmail.objects.filter(created_at__gte=last_7_days).count()
        quarantined_last_30_days = QuarantinedEmail.objects.filter(created_at__gte=last_30_days).count()
        
        # Top users by email count
        top_users = User.objects.annotate(
            email_count=models.Count('email')
        ).order_by('-email_count')[:10]
        
        top_users_list = [
            {
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'email_count': u.email_count
            }
            for u in top_users
        ]
        
        # Daily breakdown for last 7 days
        daily_stats = []
        for i in range(6, -1, -1):
            day_start = now - timedelta(days=i+1)
            day_end = now - timedelta(days=i)
            
            day_emails = Email.objects.filter(received_at__gte=day_start, received_at__lt=day_end).count()
            day_safe = ClassificationResult.objects.filter(
                email__received_at__gte=day_start,
                email__received_at__lt=day_end,
                rule_engine_verdict='safe'
            ).count()
            day_spam = ClassificationResult.objects.filter(
                email__received_at__gte=day_start,
                email__received_at__lt=day_end,
                rule_engine_verdict__in=['malicious', 'phishing', 'suspicious']
            ).count()
            
            daily_stats.append({
                'date': day_end.strftime('%Y-%m-%d'),
                'day_name': day_end.strftime('%A'),
                'total_emails': day_emails,
                'safe': day_safe,
                'spam': day_spam
            })
        
        return JsonResponse({
            'overview': {
                'total_users': total_users,
                'active_users': active_users,
                'total_emails': total_emails,
                'total_classified': total_classified,
            },
            'classification': {
                'safe': safe_count,
                'suspicious': suspicious_count,
                'phishing': phishing_count,
                'safe_percentage': (safe_count / total_classified * 100) if total_classified > 0 else 0,
                'spam_percentage': ((suspicious_count + phishing_count) / total_classified * 100) if total_classified > 0 else 0,
            },
            'recent_activity': {
                'emails_last_7_days': emails_last_7_days,
                'emails_last_30_days': emails_last_30_days,
                'quarantined_last_7_days': quarantined_last_7_days,
                'quarantined_last_30_days': quarantined_last_30_days,
            },
            'top_users': top_users_list,
            'daily_stats': daily_stats,
        })
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
@require_auth
def admin_rules_config(request):
    """Get current spam detection rules configuration - admin only."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        # Return current rule configuration
        # In a real system, these would be stored in database
        rules = {
            'phishing_threshold': {
                'auth_score_min': 20,
                'auth_failures_min': 3,
                'url_malicious_min': 1,
                'description': 'Emails below this threshold are marked as phishing'
            },
            'suspicious_threshold': {
                'auth_score_min': 30,
                'auth_failures_min': 2,
                'url_suspicious_min': 2,
                'description': 'Emails below this threshold are marked as suspicious'
            },
            'safe_threshold': {
                'auth_score_min': 60,
                'auth_passes_min': 2,
                'description': 'Emails above this threshold are marked as safe'
            },
            'known_domains': {
                'enabled': True,
                'bonus_score': 15,
                'description': 'Known legitimate domains get bonus score'
            }
        }
        
        return JsonResponse({"rules": rules})
    except Exception as e:
        logger.error(f"Error getting rules: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "PUT"])
@require_auth
def admin_rules_update(request):
    """Update spam detection rules - admin only."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        
        # In a real system, these would be saved to database
        # For now, just return success
        logger.info(f"Rules updated by admin {request.user.id}: {data}")
        
        return JsonResponse({
            "success": True,
            "message": "Rules updated successfully (Note: In production, these would be saved to database)"
        })
    except Exception as e:
        logger.error(f"Error updating rules: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

