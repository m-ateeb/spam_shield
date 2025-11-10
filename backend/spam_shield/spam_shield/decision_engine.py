from email_connector.db_utils import syslog
from email_connector.models import Email, EmailAuthResult, URLAnalysis, ClassificationResult, QuarantinedEmail
from email_connector.oauth_utils import execute_email_action
from datetime import datetime


def run_rule_based_classification(email_id: int):
    """
    Combine Module 2 + Module 3 results to classify email.
    Stores result into classification_results table and updates quarantine if needed.
    """
    try:
        # Get email object
        try:
            email_obj = Email.objects.get(id=email_id)
        except Email.DoesNotExist:
            syslog("email_not_found", "run_rule_based_classification", {"email_id": email_id})
            return None

        # Get auth results - must exist for classification
        try:
            auth_result = email_obj.auth_result
            spf = auth_result.spf_status
            dkim = auth_result.dkim_status
            dmarc = auth_result.dmarc_status
        except EmailAuthResult.DoesNotExist:
            # Authentication results must exist - do not classify without them
            syslog("classification_deferred", "run_rule_based_classification", {
                "email_id": email_id,
                "message": "Classification deferred - authentication results not available"
            })
            return None

        # Get URL analysis results
        url_analyses = URLAnalysis.objects.filter(email=email_obj)
        url_results = [u.final_verdict for u in url_analyses]
        url_pending = url_results.count("pending")
        url_safe = url_results.count("safe")
        url_suspicious = url_results.count("suspicious")
        url_malicious = url_results.count("malicious")

        # If URLs are still being analyzed, DO NOT classify - return None to indicate analysis incomplete
        # Only proceed if we have complete analysis or no URLs to analyze
        has_urls = len(url_results) > 0
        if has_urls and url_pending > 0:
            # URLs are still being analyzed - do not return any result
            syslog(
                "classification_deferred",
                "run_rule_based_classification",
                {
                    "email_id": email_id,
                    "pending_urls": url_pending,
                    "message": "Classification deferred until URL analysis completes"
                },
            )
            return None  # Return None to indicate analysis is not complete

        # Calculate auth score from email object
        auth_score = email_obj.auth_score
        
        verdict = "safe"
        action = "allow"
        reason = ""
        
        # Count authentication failures (only count actual failures, not "none" or "unknown")
        auth_failures = sum(1 for s in [spf, dkim, dmarc] if s in ["fail", "reject", "quarantine"])
        auth_passes = sum(1 for s in [spf, dkim, dmarc] if s == "pass")
        auth_unknown = sum(1 for s in [spf, dkim, dmarc] if s in ["unknown", "none"])
        
        # Check for known legitimate domains (major email providers)
        sender_domain = email_obj.sender.split('@')[-1] if '@' in email_obj.sender else ''
        known_legitimate_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 
            'protonmail.com', 'aol.com', 'mail.com', 'zoho.com', 'yandex.com',
            'netflix.com', 'amazon.com', 'microsoft.com', 'google.com', 'apple.com',
            'facebook.com', 'twitter.com', 'linkedin.com', 'github.com', 'paypal.com'
        ]
        is_known_legitimate = sender_domain.lower() in known_legitimate_domains
        
        # Determine verdict based on score thresholds:
        # Score < 20: Phishing
        # Score 20-40: Spam (Suspicious)
        # Score >= 40: Safe
        
        # First check for malicious URLs - always phishing regardless of score
        if url_malicious > 0:
            verdict = "phishing"
            action = "delete"
            reason = f"Malicious URLs detected ({url_malicious} malicious URL(s))"
        # Score-based classification
        elif auth_score < 20:
            # Score < 20: Phishing
            verdict = "phishing"
            action = "delete"
            reason = f"Very low authenticity score ({auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        elif auth_score < 40:
            # Score 20-40: Spam (Suspicious)
            verdict = "suspicious"
            action = "quarantine"
            reason = f"Low authenticity score ({auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        else:
            # Score >= 40: Safe
            verdict = "safe"
            action = "allow"
            reason = f"Passed authenticity checks (Score: {auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"

        # Create or update classification result
        ClassificationResult.objects.update_or_create(
            email=email_obj,
            defaults={
                "rule_engine_verdict": verdict,
                "final_action": action,
                "reason": reason,
                "confidence_score": 0.0,
            }
        )

        if action in ["quarantine", "delete"]:
            quarantine_email(email_obj, action, reason)
            # Execute the action on the email
            execute_email_action(email_id, action)

        syslog(
            "classification_result",
            "run_rule_based_classification",
            {
                "email_id": email_id,
                "verdict": verdict,
                "action": action,
                "spf": spf,
                "dkim": dkim,
                "dmarc": dmarc,
                "urls": {"safe": url_safe, "sus": url_suspicious, "mal": url_malicious},
            },
        )

        return {"email_id": email_id, "verdict": verdict, "action": action, "reason": reason}

    except Exception as e:
        syslog("decision_engine_error", "run_rule_based_classification", {"error": str(e)})
        return None


def quarantine_email(email_obj, action, reason):
    """Move suspicious or malicious emails into quarantine repository."""
    try:
        QuarantinedEmail.objects.create(
            email=email_obj,
            user=email_obj.user,
            reason=reason,
            status="pending" if action == "quarantine" else "deleted",
        )

        email_obj.is_suspicious = True
        email_obj.save()

        syslog("quarantine_add", "quarantine_email", {"email_id": email_obj.id, "reason": reason})
    except Exception as e:
        syslog("quarantine_error", "quarantine_email", {"email_id": email_obj.id, "error": str(e)})