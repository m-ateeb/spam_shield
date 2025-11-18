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
            # Get pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            page_size = min(page_size, 100)  # Max 100 per page
            
            # Base query - filter out invalid emails
            base_query = QuarantinedEmail.objects.filter(
                user=request.user,
                status='pending',
                email__isnull=False,  # Must have email object
            ).exclude(
                email__sender__in=['', 'Unknown']  # Exclude empty or Unknown senders
            ).select_related('email', 'email__classification').order_by('-created_at')
            
            # Get total count before pagination
            total_count = base_query.count()
            
            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size
            
            emails = base_query[start:end]
            
            # Deduplicate: Use message_id first, then fallback to sender+subject+date
            seen_message_ids = {}
            seen_content_hash = {}  # Fallback for emails with different message_ids but same content
            result = []
            
            for quarantine_record in emails:
                email_obj = quarantine_record.email
                if not email_obj:
                    continue
                
                # Skip emails with invalid sender
                if not email_obj.sender or email_obj.sender.strip() == '' or email_obj.sender == 'Unknown':
                    continue
                
                message_id = email_obj.message_id
                received_time = email_obj.received_at or quarantine_record.created_at
                
                # Create content hash for deduplication (sender + subject + date rounded to minute)
                if received_time:
                    rounded_time = received_time.replace(second=0, microsecond=0)
                    time_str = rounded_time.isoformat()
                else:
                    time_str = ''
                
                content_hash = (
                    email_obj.sender.lower().strip(),
                    (email_obj.subject or '').strip(),
                    time_str
                )
                
                # First check by message_id (most reliable)
                if message_id in seen_message_ids:
                    existing_record = seen_message_ids[message_id]
                    if quarantine_record.created_at > existing_record['created_at']:
                        # Remove the old one from result
                        result = [r for r in result if r['id'] != existing_record['id']]
                        seen_message_ids[message_id] = {
                            'id': quarantine_record.id,
                            'created_at': quarantine_record.created_at
                        }
                    else:
                        # Skip this duplicate
                        continue
                # Then check by content hash (for emails that might have different message_ids)
                elif content_hash in seen_content_hash:
                    existing_record = seen_content_hash[content_hash]
                    if quarantine_record.created_at > existing_record['created_at']:
                        # Remove the old one from result
                        result = [r for r in result if r['id'] != existing_record['id']]
                        seen_content_hash[content_hash] = {
                            'id': quarantine_record.id,
                            'created_at': quarantine_record.created_at
                        }
                    else:
                        # Skip this duplicate
                        continue
                else:
                    # New unique email
                    seen_message_ids[message_id] = {
                        'id': quarantine_record.id,
                        'created_at': quarantine_record.created_at
                    }
                    seen_content_hash[content_hash] = {
                        'id': quarantine_record.id,
                        'created_at': quarantine_record.created_at
                    }
                
                # Get threat type and confidence from classification if available
                threat_type = 'unknown'
                confidence_score = 0
                if hasattr(email_obj, 'classification'):
                    threat_type = email_obj.classification.rule_engine_verdict
                    confidence_score = email_obj.classification.confidence_score
                
                # Build headers object
                from email_connector.utils import extract_display_name
                display_name = extract_display_name(email_obj.from_header) if email_obj.from_header else ""
                
                headers = {
                    'from': email_obj.from_header or email_obj.sender,
                    'reply_to': email_obj.reply_to or '',
                    'return_path': email_obj.return_path or '',
                    'subject': email_obj.subject or '(No subject)',
                }
                
                # Format sender: "Display Name <email@domain.com>" or just "email@domain.com"
                sender_display = f"{display_name} <{email_obj.sender}>" if display_name else email_obj.sender
                
                result.append({
                    'id': quarantine_record.id,
                    'email_id': email_obj.id,
                    'sender': email_obj.sender,  # Always store email address
                    'sender_display': sender_display,  # Display format with name if available
                    'subject': email_obj.subject or '(No subject)',
                    'date': quarantine_record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'received_at': email_obj.received_at.strftime('%Y-%m-%d %H:%M:%S') if email_obj.received_at else None,
                    'threat': threat_type,
                    'score': int(confidence_score),
                    'reason': quarantine_record.reason,
                    'status': quarantine_record.status,
                    # Full email details
                    'body_html': email_obj.body_html or '',
                    'highlighted_body_html': email_obj.highlighted_body_html or email_obj.body_html or '',
                    'headers': headers,
                    'auth_score': email_obj.auth_score,
                    'spf_result': email_obj.spf_result,
                    'dkim_result': email_obj.dkim_result,
                    'dmarc_policy': email_obj.dmarc_policy,
                })
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            
            return JsonResponse({
                'quarantined': result,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_previous': page > 1,
                }
            })
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

