# email_connector/extension_views.py
"""
Extension-specific API endpoints for browser extension
"""
import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .auth_utils import require_auth
from .db_utils import syslog
from .models import ConnectedAccount, Email, EmailAuthResult, URLAnalysis, ClassificationResult
from .email_validator import validate_email_authenticity
from .url_reputation import extract_urls_from_html, analyze_url
from spam_shield.decision_engine import run_rule_based_classification
import dns.resolver
import re

logger = logging.getLogger(__name__)


def validate_email_domain_authenticity(sender_domain: str, from_address: str, subject: str, body_html: str):
    """
    Validate email authenticity using domain checks and heuristics.
    Used when raw email is not available (extension mode).
    """
    results = {
        "spf_result": "unknown",
        "dkim_result": "unknown",
        "dmarc_policy": "unknown",
        "auth_score": 50,
        "validation_summary": ""
    }
    
    if not sender_domain:
        results["validation_summary"] = "Invalid sender domain"
        results["auth_score"] = 0
        return results
    
    # === SPF CHECK (DNS-based) ===
    try:
        txt_records = dns.resolver.resolve(sender_domain, "TXT")
        spf_found = any("v=spf1" in r.to_text() for r in txt_records)
        if spf_found:
            # Check if SPF record is properly configured
            spf_record = next((r.to_text() for r in txt_records if "v=spf1" in r.to_text()), "")
            # If SPF exists, assume pass (we can't verify without raw email)
            results["spf_result"] = "pass"
        else:
            results["spf_result"] = "none"
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception) as e:
        results["spf_result"] = "fail"
        logger.debug(f"SPF check failed for {sender_domain}: {e}")
    
    # === DMARC CHECK (DNS-based) ===
    try:
        dmarc_record = dns.resolver.resolve(f"_dmarc.{sender_domain}", "TXT")
        dmarc_txt = next((r.to_text() for r in dmarc_record if "v=DMARC1" in r.to_text()), None)
        if dmarc_txt:
            policy_match = re.search(r"p=([^;]+)", dmarc_txt)
            results["dmarc_policy"] = policy_match.group(1) if policy_match else "none"
        else:
            results["dmarc_policy"] = "none"
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception) as e:
        results["dmarc_policy"] = "none"
        logger.debug(f"DMARC check failed for {sender_domain}: {e}")
    
    # === DKIM CHECK (can't verify without raw email, but check if domain has DKIM records) ===
    try:
        # Check for DKIM selector records (common selectors: default, google, mail)
        dkim_selectors = ["default", "google", "mail", "selector1", "selector2"]
        dkim_found = False
        for selector in dkim_selectors:
            try:
                dkim_record = dns.resolver.resolve(f"{selector}._domainkey.{sender_domain}", "TXT")
                if dkim_record:
                    dkim_found = True
                    break
            except:
                continue
        # If DKIM records exist, mark as pass (we can't fully verify without raw email)
        results["dkim_result"] = "pass" if dkim_found else "unknown"
    except Exception as e:
        results["dkim_result"] = "unknown"
        logger.debug(f"DKIM check failed for {sender_domain}: {e}")
    
    # === HEURISTIC CHECKS ===
    heuristic_score = 0
    
    # Check for suspicious patterns in subject
    suspicious_subject_patterns = [
        r'urgent', r'act now', r'click here', r'verify.*account', r'limited time',
        r'winner', r'prize', r'congratulations', r'free.*money', r'claim.*now'
    ]
    subject_lower = subject.lower()
    suspicious_subject_count = sum(1 for pattern in suspicious_subject_patterns if re.search(pattern, subject_lower))
    if suspicious_subject_count > 0:
        heuristic_score -= (suspicious_subject_count * 5)
    
    # Check sender domain reputation (common free email domains and major companies are less suspicious)
    known_legitimate_domains = [
        'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'protonmail.com',
        'aol.com', 'mail.com', 'zoho.com', 'yandex.com',
        'netflix.com', 'amazon.com', 'microsoft.com', 'google.com', 'apple.com',
        'facebook.com', 'twitter.com', 'linkedin.com', 'github.com', 'paypal.com',
        'ebay.com', 'shopify.com', 'stripe.com', 'adobe.com', 'dropbox.com'
    ]
    if sender_domain.lower() in known_legitimate_domains:
        heuristic_score += 15  # Significant positive for known providers/companies
    
    # Check for suspicious domains (new TLDs, misspellings)
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz']
    if any(sender_domain.lower().endswith(tld) for tld in suspicious_tlds):
        heuristic_score -= 10
    
    # === SCORE CALCULATION ===
    score_map = {"pass": 33, "fail": 0, "none": 10, "quarantine": 15, "reject": 20, "unknown": 5}
    base_score = (
        score_map.get(results["spf_result"], 0) +
        score_map.get(results["dkim_result"], 0) +
        score_map.get(results["dmarc_policy"], 0)
    )
    
    # Add heuristic adjustments
    results["auth_score"] = max(0, min(100, base_score + heuristic_score))
    
    results["validation_summary"] = (
        f"SPF={results['spf_result']}, DKIM={results['dkim_result']}, "
        f"DMARC={results['dmarc_policy']}, SCORE={results['auth_score']}"
    )
    
    return results


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def analyze_email_extension(request):
    """
    Real-time email analysis endpoint for browser extension.
    Receives email data from content script and returns instant verdict.
    """
    try:
        data = json.loads(request.body)
        
        # Extract email data
        message_id = data.get('message_id')
        subject = data.get('subject', '')
        from_address = data.get('from', '')
        body_html = data.get('body_html', '')
        headers = data.get('headers', {})
        provider = data.get('provider', 'unknown')

        if not message_id:
            return JsonResponse({'error': 'Missing message_id'}, status=400)

        # Check if already analyzed (cache check)
        try:
            existing_email = Email.objects.filter(message_id=message_id).first()
            if existing_email:
                # CRITICAL: Only mark as opened if user is actually viewing the email
                # This endpoint is called when user opens an email in Gmail/Outlook
                # So it's safe to mark as opened here
                if not existing_email.opened_at:
                    existing_email.opened_at = timezone.now()
                    existing_email.save(update_fields=['opened_at'])
                    syslog("email_opened", "analyze_email_extension", {
                        "email_id": existing_email.id,
                        "message_id": message_id,
                        "note": "Email marked as opened via extension"
                    })
                
                # Email already analyzed, return cached result
                result = get_analysis_result(existing_email.id)
                return JsonResponse(result)
        except Exception as e:
            logger.warning(f"Error checking existing email: {e}")

        # Get connected account
        try:
            account = ConnectedAccount.objects.filter(
                user_id=request.user_id,
                provider=provider
            ).first()
        except Exception as e:
            logger.error(f"Error getting connected account: {e}")
            account = None

        if not account:
            return JsonResponse({
                'error': 'No connected account found',
                'verdict': 'unknown',
                'action': 'none'
            }, status=404)

        # === EMAIL AUTHENTICATION ===
        sender_domain = from_address.split('@')[-1] if '@' in from_address else ''
        
        # Perform domain-based validation (can check SPF/DMARC records without raw email)
        auth_result = validate_email_domain_authenticity(sender_domain, from_address, subject, body_html)

        # === SAVE EMAIL TO DATABASE ===
        from django.contrib.auth.models import User
        user = User.objects.get(id=request.user_id)
        
        email_obj = Email.objects.create(
            user=user,
            account=account,
            message_id=message_id,
            subject=subject,
            sender=from_address,
            from_header=from_address,
            reply_to=headers.get("reply_to", "") or None,
            return_path=headers.get("return_path", "") or None,
            body_html=body_html,
            highlighted_body_html=body_html,
            received_at=timezone.now(),
            opened_at=timezone.now(),  # Mark as opened since user is viewing it
            spf_result=auth_result["spf_result"],
            dkim_result=auth_result["dkim_result"],
            dmarc_policy=auth_result["dmarc_policy"],
            auth_score=auth_result["auth_score"],
            is_suspicious=False,  # Don't mark as suspicious until full analysis is complete
        )
        
        # Log that email was opened
        syslog("email_opened", "analyze_email_extension", {
            "email_id": email_obj.id,
            "message_id": message_id
        })
        email_id = email_obj.id

        # === INSERT AUTH RESULTS ===
        EmailAuthResult.objects.create(
            email=email_obj,
            spf_status=auth_result["spf_result"],
            dkim_status=auth_result["dkim_result"],
            dmarc_status=auth_result["dmarc_policy"],
            validation_summary=auth_result["validation_summary"],
        )

        # === URL ANALYSIS ===
        urls = extract_urls_from_html(body_html)
        url_verdicts = []
        
        for url in urls[:5]:  # Limit to 5 URLs for performance
            url_result = analyze_url(url, email_id)
            URLAnalysis.objects.create(
                email=email_obj,
                url=url,
                source="body",
                google_safebrowsing=url_result.get("google_safebrowsing", ""),
                urlhaus_status=url_result.get("urlhaus_status", ""),
                urlscan_status=url_result.get("urlscan_status", ""),
                final_verdict=url_result.get("final_verdict", "safe"),
            )
            url_verdicts.append(url_result.get("final_verdict", "safe"))

        # === RUN DECISION ENGINE ===
        # CRITICAL: Check if URL analysis is complete before running classification
        url_analyses = URLAnalysis.objects.filter(email=email_obj)
        url_results = [u.final_verdict for u in url_analyses]
        url_pending = url_results.count("pending")
        
        # If URLs are still being analyzed, return pending status - DO NOT classify yet
        if len(url_results) > 0 and url_pending > 0:
            return JsonResponse({
                'email_id': email_id,
                'verdict': 'pending',
                'action': 'none',
                'reason': f'URL analysis in progress ({url_pending} pending)',
                'auth_score': auth_result['auth_score'],
                'urls_analyzed': len(urls),
                'analysis_complete': False,  # Explicitly mark as incomplete
            })
        
        # Run classification only when analysis is complete
        classification_result = run_rule_based_classification(email_id)

        # If classification returned None, analysis is not complete - return pending
        if not classification_result:
            return JsonResponse({
                'email_id': email_id,
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Analysis in progress - please wait',
                'auth_score': auth_result['auth_score'],
                'urls_analyzed': len(urls),
                'analysis_complete': False,  # Explicitly mark as incomplete
            })
        
        # CRITICAL: Double-check that classification is actually complete
        # Verify that we have a classification result AND it's not based on incomplete data
        try:
            classification_obj = ClassificationResult.objects.get(email=email_obj)
            # Verify URL analysis is still complete (no new pending URLs)
            url_analyses_check = URLAnalysis.objects.filter(email=email_obj)
            url_results_check = [u.final_verdict for u in url_analyses_check]
            url_pending_check = url_results_check.count("pending")
            
            # If URLs became pending again, return pending
            if len(url_results_check) > 0 and url_pending_check > 0:
                return JsonResponse({
                    'email_id': email_id,
                    'verdict': 'pending',
                    'action': 'none',
                    'reason': 'URL analysis still in progress',
                    'auth_score': auth_result['auth_score'],
                    'urls_analyzed': len(urls),
                    'analysis_complete': False,
                })
        except ClassificationResult.DoesNotExist:
            # No classification yet, return pending
            return JsonResponse({
                'email_id': email_id,
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Classification not yet complete',
                'auth_score': auth_result['auth_score'],
                'urls_analyzed': len(urls),
                'analysis_complete': False,
            })

        # === RETURN RESULT ===
        # Only return final result if analysis is 100% complete
        # Get the saved classification to include confidence_score
        try:
            saved_classification = ClassificationResult.objects.get(email=email_obj)
            confidence_score = saved_classification.confidence_score
        except ClassificationResult.DoesNotExist:
            confidence_score = classification_result.get('confidence', 0.0)
        
        response = {
            'email_id': email_id,
            'verdict': classification_result['verdict'],
            'action': classification_result['action'],
            'reason': classification_result['reason'],
            'confidence_score': confidence_score,
            'auth_score': auth_result['auth_score'],
            'urls_analyzed': len(urls),
            'url_analysis': f"{url_verdicts.count('safe')} safe, {url_verdicts.count('suspicious')} suspicious, {url_verdicts.count('malicious')} malicious",
            'analysis_complete': True,  # Mark as complete only when all analysis is done
        }

        syslog("extension_analysis", "analyze_email_extension", {
            "email_id": email_id,
            "verdict": classification_result['verdict'],
            "provider": provider
        })

        return JsonResponse(response)

    except Exception as e:
        logger.error(f"Extension analysis error: {str(e)}")
        syslog("extension_error", "analyze_email_extension", {"error": str(e)})
        return JsonResponse({
            'error': 'Analysis failed',
            'verdict': 'unknown',
            'action': 'none',
            'reason': str(e)
        }, status=500)


def get_analysis_result(email_id: int) -> dict:
    """Get existing analysis result for an email - only if analysis is complete"""
    try:
        # Get email object
        try:
            email_obj = Email.objects.get(id=email_id)
        except Email.DoesNotExist:
            return {
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Email not found',
                'analysis_complete': False,
            }

        # Check if URL analysis is complete
        url_analyses = email_obj.url_analyses.all()
        url_verdicts = [u.final_verdict for u in url_analyses]
        url_pending = url_verdicts.count("pending")
        
        # If URLs are still being analyzed, return pending - DO NOT return any verdict
        if len(url_verdicts) > 0 and url_pending > 0:
            return {
                'verdict': 'pending',
                'action': 'none',
                'reason': f'URL analysis in progress ({url_pending} pending)',
                'analysis_complete': False,
            }

        # Get classification result - must exist for complete analysis
        try:
            classification = email_obj.classification
        except ClassificationResult.DoesNotExist:
            return {
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Analysis in progress',
                'analysis_complete': False,
            }

        # Verify authentication results exist
        try:
            auth_result = email_obj.auth_result
        except:
            return {
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Authentication analysis in progress',
                'analysis_complete': False,
            }

        # Get email details
        auth_score = email_obj.auth_score

        # Return complete result only when all analysis is done
        return {
            'email_id': email_id,
            'verdict': classification.rule_engine_verdict,
            'action': classification.final_action,
            'reason': classification.reason,
            'confidence_score': classification.confidence_score,
            'auth_score': auth_score,
            'urls_analyzed': len(url_verdicts),
            'url_analysis': f"{url_verdicts.count('safe')} safe, {url_verdicts.count('suspicious')} suspicious, {url_verdicts.count('malicious')} malicious",
            'analysis_complete': True,  # Mark as complete
        }

    except Exception as e:
        logger.error(f"Error getting analysis result: {str(e)}")
        return {
            'verdict': 'pending',
            'action': 'none',
            'reason': 'Analysis in progress',
            'analysis_complete': False,
        }


@require_http_methods(["GET"])
@require_auth
def extension_health_check(request):
    """Health check endpoint for extension to verify backend connectivity"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': request.user_id
    })

