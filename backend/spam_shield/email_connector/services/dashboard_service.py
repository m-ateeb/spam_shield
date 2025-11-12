"""
Dashboard service for statistics and summaries
"""
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from ..models import ConnectedAccount, Email, QuarantinedEmail, ClassificationResult
import logging

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data"""
    
    @staticmethod
    def get_user_summary(user):
        """Get user dashboard summary"""
        try:
            now = timezone.now()
            last_30_days = now - timedelta(days=30)
            
            total_emails = Email.objects.filter(user=user).count()
            total_last_month = Email.objects.filter(
                user=user,
                received_at__gte=last_30_days
            ).count()
            
            spam_blocked = QuarantinedEmail.objects.filter(
                user=user,
                status='pending'
            ).count()
            
            clean_emails = Email.objects.filter(
                user=user,
                classification__rule_engine_verdict='safe'
            ).count()
            
            clean_last_month = Email.objects.filter(
                user=user,
                classification__rule_engine_verdict='safe',
                received_at__gte=last_30_days
            ).count()
            
            safe_count = ClassificationResult.objects.filter(
                email__user=user,
                rule_engine_verdict='safe'
            ).count()
            total_classified = ClassificationResult.objects.filter(
                email__user=user
            ).count()
            
            success_rate = (safe_count / total_classified * 100) if total_classified > 0 else 0
            
            return {
                'user_email': user.email,
                'user_name': user.get_full_name() or user.username,
                'total_emails': total_emails,
                'total_emails_change': f"+{total_last_month} in last 30 days",
                'spam_blocked': spam_blocked,
                'spam_blocked_pct': f"{(spam_blocked / total_emails * 100) if total_emails > 0 else 0:.1f}% of total",
                'clean_inbox': clean_emails,
                'clean_inbox_change': f"+{clean_last_month} in last 30 days",
                'success_rate': f"{success_rate:.1f}%",
                'success_rate_change': "No change",
                'quarantined_emails': spam_blocked,
                'suspicious_emails': ClassificationResult.objects.filter(
                    email__user=user,
                    rule_engine_verdict='suspicious'
                ).count(),
            }
        except Exception as e:
            logger.error(f"Error getting user summary: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_admin_summary():
        """Get admin dashboard summary"""
        try:
            now = timezone.now()
            last_30_days = now - timedelta(days=30)
            
            total_users = User.objects.count()
            total_last_month = User.objects.filter(
                date_joined__gte=last_30_days
            ).count()
            
            active_users = ConnectedAccount.objects.values('user').distinct().count()
            active_pct = (active_users / total_users * 100) if total_users > 0 else 0
            
            emails_quarantined = QuarantinedEmail.objects.filter(status='pending').count()
            emails_last_month = QuarantinedEmail.objects.filter(
                status='pending',
                created_at__gte=last_30_days
            ).count()
            
            safe_count = ClassificationResult.objects.filter(
                rule_engine_verdict='safe'
            ).count()
            total_classified = ClassificationResult.objects.count()
            system_success_rate = (safe_count / total_classified * 100) if total_classified > 0 else 0
            
            return {
                'total_users': total_users,
                'total_users_change': f"+{total_last_month} in last 30 days",
                'active_users': active_users,
                'active_users_pct': f"{active_pct:.1f}% active rate",
                'emails_quarantined': emails_quarantined,
                'emails_quarantined_change': f"+{emails_last_month} in last 30 days",
                'system_success_rate': f"{system_success_rate:.1f}%",
                'system_success_rate_change': "No change",
            }
        except Exception as e:
            logger.error(f"Error getting admin summary: {e}", exc_info=True)
            raise

