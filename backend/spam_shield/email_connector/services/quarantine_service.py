"""
Service for quarantine operations
"""
from django.http import JsonResponse
from ..models import QuarantinedEmail
from ..auth_utils import require_auth
import logging

logger = logging.getLogger(__name__)


class QuarantineService:
    """Service for managing quarantined emails"""
    
    @staticmethod
    @require_auth
    def list_quarantined_emails(request):
        """List all quarantined emails for the authenticated user"""
        try:
            emails = QuarantinedEmail.objects.filter(
                user=request.user
            ).order_by('-created_at')[:100]
            
            result = []
            for email in emails:
                # Get threat type and confidence from classification if available
                threat_type = 'unknown'
                confidence_score = 0
                if email.email and hasattr(email.email, 'classification'):
                    threat_type = email.email.classification.rule_engine_verdict
                    confidence_score = email.email.classification.confidence_score
                
                result.append({
                    'id': email.id,
                    'email_id': email.email.id if email.email else None,
                    'sender': email.email.sender if email.email else 'Unknown',
                    'subject': email.email.subject if email.email else 'No subject',
                    'date': email.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'threat': threat_type,
                    'score': int(confidence_score),
                    'reason': email.reason,
                    'status': email.status,
                })
            
            return JsonResponse({'quarantined': result})
        except Exception as e:
            logger.error(f"Error listing quarantined emails: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    @staticmethod
    @require_auth
    def release_email(request, email_id):
        """Release a quarantined email"""
        try:
            quarantined = QuarantinedEmail.objects.get(
                id=email_id,
                user=request.user,
                status='pending'
            )
            quarantined.status = 'released'
            quarantined.save()
            return JsonResponse({'success': True})
        except QuarantinedEmail.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
        except Exception as e:
            logger.error(f"Error releasing email: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    @staticmethod
    @require_auth
    def delete_email(request, email_id):
        """Permanently delete a quarantined email"""
        try:
            quarantined = QuarantinedEmail.objects.get(
                id=email_id,
                user=request.user,
                status='pending'
            )
            quarantined.status = 'deleted'
            quarantined.save()
            return JsonResponse({'success': True})
        except QuarantinedEmail.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting email: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

