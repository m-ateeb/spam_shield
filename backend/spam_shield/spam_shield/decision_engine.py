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

        # Get auth results
        try:
            auth_result = email_obj.auth_result
            spf = auth_result.spf_status
            dkim = auth_result.dkim_status
            dmarc = auth_result.dmarc_status
        except EmailAuthResult.DoesNotExist:
            spf = "unknown"
            dkim = "unknown"
            dmarc = "unknown"

        # Get URL analysis results
        url_analyses = URLAnalysis.objects.filter(email=email_obj)
        url_results = [u.final_verdict for u in url_analyses]
        url_safe = url_results.count("safe")
        url_suspicious = url_results.count("suspicious")
        url_malicious = url_results.count("malicious")

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
        
        # Determine verdict based on multiple factors (more lenient for legitimate emails)
        if url_malicious > 0:
            # Malicious URLs are always a red flag
            verdict = "phishing"
            action = "delete"
            reason = f"Malicious URLs detected ({url_malicious} malicious URL(s))"
        elif auth_score < 20 or (auth_failures >= 3 and not is_known_legitimate):
            # Very low score or multiple failures (unless from known legitimate domain)
            verdict = "phishing"
            action = "delete"
            reason = f"Very low authenticity score ({auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        elif url_suspicious > 2 or (auth_score < 30 and auth_failures >= 2 and not is_known_legitimate):
            # Multiple suspicious URLs or low score with failures (unless from known domain)
            verdict = "suspicious"
            action = "quarantine"
            if url_suspicious > 2:
                reason = f"Multiple suspicious URLs detected ({url_suspicious} suspicious URL(s))"
            else:
                reason = f"Low authenticity score ({auth_score}/100) with authentication failures"
        elif url_suspicious > 0 and auth_score < 40 and not is_known_legitimate:
            # Suspicious URLs with low score (unless from known domain)
            verdict = "suspicious"
            action = "quarantine"
            reason = f"Suspicious URLs detected ({url_suspicious} suspicious URL(s)) with moderate authenticity"
        elif auth_passes >= 2 and auth_score >= 60:
            # Good authentication
            verdict = "safe"
            action = "allow"
            reason = f"Passed authenticity checks (Score: {auth_score}/100) - SPF:{spf}, DKIM:{dkim}, DMARC:{dmarc}"
        elif is_known_legitimate and auth_score >= 30:
            # Known legitimate domain with reasonable score
            verdict = "safe"
            action = "allow"
            reason = f"From trusted domain ({sender_domain}) - Score: {auth_score}/100"
        else:
            # Default to safe (more lenient)
            verdict = "safe"
            action = "allow"
            reason = f"Passed basic checks (Score: {auth_score}/100)"

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