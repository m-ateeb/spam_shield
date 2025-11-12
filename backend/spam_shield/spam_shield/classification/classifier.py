"""
Main classification logic
"""
from email_connector.db_utils import syslog
from email_connector.models import Email, EmailAuthResult, URLAnalysis, ClassificationResult, QuarantinedEmail
from .rules import (
    count_auth_results,
    count_url_results,
    is_known_legitimate_domain,
    classify_by_malicious_urls,
    classify_by_auth_score,
)


def get_email_data(email_id: int) -> tuple:
    """Get email and related data"""
    try:
        email_obj = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        syslog("email_not_found", "get_email_data", {"email_id": email_id})
        return None, None, None
    
    try:
        auth_result = email_obj.auth_result
    except EmailAuthResult.DoesNotExist:
        syslog("classification_deferred", "get_email_data", {
            "email_id": email_id,
            "message": "Classification deferred - authentication results not available"
        })
        return None, None, None
    
    url_analyses = URLAnalysis.objects.filter(email=email_obj)
    return email_obj, auth_result, url_analyses


def check_url_analysis_complete(url_analyses) -> bool:
    """Check if URL analysis is complete"""
    url_counts = count_url_results(url_analyses)
    has_urls = url_counts['total'] > 0
    if has_urls and url_counts['pending'] > 0:
        syslog("classification_deferred", "check_url_analysis_complete", {
            "pending_urls": url_counts['pending'],
            "message": "Classification deferred until URL analysis completes"
        })
        return False
    return True


def calculate_classification(email_obj, auth_result, url_analyses) -> dict:
    """Calculate email classification"""
    spf = auth_result.spf_status
    dkim = auth_result.dkim_status
    dmarc = auth_result.dmarc_status
    auth_score = email_obj.auth_score
    
    auth_counts = count_auth_results(spf, dkim, dmarc)
    url_counts = count_url_results(url_analyses)
    
    # Check for malicious URLs first
    verdict, action, reason, confidence = classify_by_malicious_urls(url_counts['malicious'])
    if verdict:
        return {
            'verdict': verdict,
            'action': action,
            'reason': reason,
            'confidence': confidence,
        }
    
    # Apply known domain bonus
    if is_known_legitimate_domain(email_obj.sender):
        auth_score = min(100, auth_score + 10)
    
    # Classify by auth score
    verdict, action, reason, confidence = classify_by_auth_score(
        auth_score, auth_counts, spf, dkim, dmarc
    )
    
    # Adjust confidence based on URL analysis and auth results
    if url_counts['suspicious'] > 0:
        if verdict in ["phishing", "suspicious"]:
            confidence = min(95.0, confidence + (url_counts['suspicious'] * (3.0 if verdict == "suspicious" else 2.0)))
        else:
            confidence = max(70.0, confidence - (url_counts['suspicious'] * 2.0))
        reason += f" + {url_counts['suspicious']} suspicious URL(s)"
    
    # Adjust confidence based on authentication results
    if verdict in ["phishing", "suspicious"]:
        if auth_counts['failures'] >= 2:
            confidence = min(95.0, confidence + 5.0)
        elif auth_counts['failures'] == 1:
            confidence = min(95.0, confidence + 2.0)
    elif verdict == "safe":
        if auth_counts['passes'] >= 2:
            confidence = min(95.0, confidence + 5.0)
        elif auth_counts['passes'] == 1:
            confidence = min(95.0, confidence + 2.0)
    
    # Ensure confidence is within valid range
    confidence = max(50.0, min(100.0, confidence))
    
    return {
        'verdict': verdict,
        'action': action,
        'reason': reason,
        'confidence': confidence,
    }


def save_classification_result(email_obj, classification: dict) -> ClassificationResult:
    """Save classification result to database"""
    return ClassificationResult.objects.update_or_create(
        email=email_obj,
        defaults={
            "rule_engine_verdict": classification['verdict'],
            "final_action": classification['action'],
            "reason": classification['reason'],
            "confidence_score": round(classification['confidence'], 1),
        }
    )[0]


def handle_quarantine(email_obj, classification: dict):
    """Handle email quarantine based on classification"""
    from email_connector.oauth_utils import execute_email_action
    
    if classification['action'] in ['quarantine', 'delete']:
        quarantine, created = QuarantinedEmail.objects.get_or_create(
            email=email_obj,
            user=email_obj.user,
            defaults={
                'reason': classification['reason'],
                'status': 'pending',
            }
        )
        
        if not created:
            quarantine.reason = classification['reason']
            quarantine.status = 'pending'
            quarantine.save()
        
        email_obj.is_suspicious = True
        email_obj.save()
        
        # Execute the action on the email
        execute_email_action(email_obj.id, classification['action'])

