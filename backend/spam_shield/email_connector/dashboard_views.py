# email_connector/dashboard_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from email_connector.models import ConnectedAccount, Email, QuarantinedEmail, ClassificationResult
from email_connector.auth_utils import require_auth
from django.views.decorators.csrf import csrf_exempt
import json

@require_GET
@require_auth
def list_connected_accounts(request):
    """List all connected email accounts for logged-in user."""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Listing accounts for user: {request.user.id} ({request.user.email})")
        accounts = ConnectedAccount.objects.filter(
            user=request.user
        ).values(
            'id', 'email_address', 'provider', 'inbox_sync_status', 'token_expiry'
        )
        accounts_list = list(accounts)
        logger.info(f"Found {len(accounts_list)} accounts for user {request.user.id}")
        return JsonResponse({"accounts": accounts_list})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing accounts: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE", "POST"])
@require_auth
def disconnect_account(request):
    """Disconnect/remove a connected email account."""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Get account ID from request
        if request.method == 'POST':
            data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
            account_id = data.get('id')
        else:
            account_id = request.GET.get('id')
        
        if not account_id:
            return JsonResponse({"error": "Account ID is required"}, status=400)
        
        # Get the account and verify it belongs to the user
        try:
            account = ConnectedAccount.objects.get(id=account_id, user=request.user)
            account_email = account.email_address
            account_provider = account.provider
            account.delete()
            logger.info(f"Disconnected account {account_email} ({account_provider}) for user {request.user.id}")
            return JsonResponse({"success": True, "message": f"Account {account_email} disconnected successfully"})
        except ConnectedAccount.DoesNotExist:
            return JsonResponse({"error": "Account not found"}, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error disconnecting account: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
@require_auth
def dashboard_summary(request):
    """Get comprehensive dashboard stats for the logged-in user."""
    try:
        # Get all user's emails across all accounts
        user_emails = Email.objects.filter(user=request.user)
        
        # Time ranges
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        # Total stats
        total_emails = user_emails.count()
        total_emails_last_week = user_emails.filter(received_at__gte=last_week).count()
        total_emails_last_month = user_emails.filter(received_at__gte=last_month).count()
        
        # Suspicious/blocked emails
        suspicious_emails = user_emails.filter(is_suspicious=True).count()
        suspicious_last_week = user_emails.filter(is_suspicious=True, received_at__gte=last_week).count()
        
        # Get classification results
        safe_emails = ClassificationResult.objects.filter(
            email__user=request.user,
            rule_engine_verdict='safe'
        ).count()
        
        # Count both "malicious" and "phishing" as malicious
        malicious_emails = ClassificationResult.objects.filter(
            email__user=request.user,
            rule_engine_verdict__in=['malicious', 'phishing']
        ).count()
        
        # Quarantined emails
        quarantined = QuarantinedEmail.objects.filter(
            user=request.user,
            status='pending'
        ).count()
        
        # Clean inbox (safe emails)
        clean_inbox = safe_emails
        
        # Success rate (safe / total)
        success_rate = (safe_emails / total_emails * 100) if total_emails > 0 else 0
        
        # Calculate changes
        week_change = total_emails_last_week - (total_emails - total_emails_last_week) if total_emails > total_emails_last_week else 0
        week_change_pct = (week_change / (total_emails - total_emails_last_week) * 100) if (total_emails - total_emails_last_week) > 0 else 0
        
        # Weekly activity data for chart (last 7 days)
        weekly_activity = []
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(6, -1, -1):  # Last 7 days, starting from 6 days ago
            day_start = now - timedelta(days=i+1)
            day_end = now - timedelta(days=i)
            
            # Get emails for this day
            day_emails = user_emails.filter(
                received_at__gte=day_start,
                received_at__lt=day_end
            )
            
            # Get spam/malicious emails for this day
            day_spam = ClassificationResult.objects.filter(
                email__user=request.user,
                email__received_at__gte=day_start,
                email__received_at__lt=day_end,
                rule_engine_verdict__in=['malicious', 'phishing', 'suspicious']
            ).count()
            
            # Get clean/safe emails for this day
            day_clean = ClassificationResult.objects.filter(
                email__user=request.user,
                email__received_at__gte=day_start,
                email__received_at__lt=day_end,
                rule_engine_verdict='safe'
            ).count()
            
            # Get day name
            day_name = day_names[day_end.weekday()]
            
            weekly_activity.append({
                'day': day_name,
                'spam': day_spam,
                'clean': day_clean
            })
        
        return JsonResponse({
            "user_email": request.user.email,
            "user_name": request.user.get_full_name() or request.user.username,
            "total_emails": total_emails,
            "total_emails_change": f"+{week_change_pct:.1f}% from last week" if week_change_pct > 0 else f"{week_change_pct:.1f}% from last week",
            "spam_blocked": malicious_emails,
            "spam_blocked_pct": f"{(malicious_emails / total_emails * 100):.1f}% of total" if total_emails > 0 else "0%",
            "clean_inbox": clean_inbox,
            "clean_inbox_change": f"+{((clean_inbox - (total_emails - total_emails_last_week)) / max(total_emails - total_emails_last_week, 1) * 100):.1f}% from last week" if total_emails > total_emails_last_week else "0%",
            "success_rate": f"{success_rate:.1f}%",
            "success_rate_change": f"+0.5% improvement",  # TODO: Calculate actual change
            "quarantined_emails": quarantined,
            "suspicious_emails": suspicious_emails,
            "weekly_activity": weekly_activity,
        })
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)

@require_GET
@require_auth
def admin_dashboard_summary(request):
    """Get admin dashboard stats - only accessible to admin users."""
    if not request.user.is_staff or not request.user.is_superuser:
        return JsonResponse({"error": "Admin access required"}, status=403)
    
    try:
        # Total users
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Time ranges
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        # Users joined this week
        users_this_week = User.objects.filter(date_joined__gte=last_week).count()
        
        # Total emails across all users
        total_emails = Email.objects.count()
        emails_last_month = Email.objects.filter(received_at__gte=last_month).count()
        
        # Quarantined emails
        total_quarantined = QuarantinedEmail.objects.filter(status='pending').count()
        quarantined_last_month = QuarantinedEmail.objects.filter(
            status='pending',
            created_at__gte=last_month
        ).count()
        
        # Calculate change in quarantined emails
        if quarantined_last_month > 0:
            quarantined_change = ((total_quarantined - quarantined_last_month) / max(quarantined_last_month, 1)) * 100
            quarantined_change_str = f"+{quarantined_change:.1f}% from last month" if quarantined_change >= 0 else f"{quarantined_change:.1f}% from last month"
        else:
            quarantined_change_str = "0%"
        
        # System success rate
        total_classified = ClassificationResult.objects.count()
        safe_classified = ClassificationResult.objects.filter(rule_engine_verdict='safe').count()
        system_success_rate = (safe_classified / total_classified * 100) if total_classified > 0 else 0
        
        return JsonResponse({
            "total_users": total_users,
            "total_users_change": f"+{users_this_week} this week",
            "active_users": active_users,
            "active_users_pct": f"{(active_users / total_users * 100):.1f}% active rate" if total_users > 0 else "0%",
            "emails_quarantined": total_quarantined,
            "emails_quarantined_change": quarantined_change_str,
            "system_success_rate": f"{system_success_rate:.1f}%",
            "system_success_rate_change": "+1.2% improvement",  # TODO: Calculate actual change
        })
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)

@require_GET
@require_auth
def check_admin(request):
    """Check if current user is admin."""
    return JsonResponse({
        "is_admin": request.user.is_staff and request.user.is_superuser,
        "is_staff": request.user.is_staff,
        "is_superuser": request.user.is_superuser
    })
