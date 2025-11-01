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

from .auth_utils import require_jwt
from .supabase_client import supabase, syslog
from .email_validator import validate_email_authenticity
from .url_reputation import extract_urls_from_html, analyze_url
from spam_shield.decision_engine import run_rule_based_classification

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@require_jwt
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
        existing = supabase.table("emails").select("id").eq("message_id", message_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Email already analyzed, return cached result
            email_id = existing.data[0]["id"]
            result = get_analysis_result(email_id)
            return JsonResponse(result)

        # Get connected account
        account_res = (
            supabase.table("connected_accounts")
            .select("*")
            .eq("user_id", request.user_id)
            .eq("provider", provider)
            .execute()
        )

        if not account_res.data:
            return JsonResponse({
                'error': 'No connected account found',
                'verdict': 'unknown',
                'action': 'none'
            }, status=404)

        account = account_res.data[0]

        # === EMAIL AUTHENTICATION ===
        sender_domain = from_address.split('@')[-1] if '@' in from_address else ''
        
        # For extension, we might not have raw email, so do simplified auth check
        auth_result = {
            'spf_result': 'unknown',
            'dkim_result': 'unknown',
            'dmarc_policy': 'unknown',
            'auth_score': 50,  # Neutral score
            'validation_summary': 'Limited validation (extension mode)'
        }

        # === SAVE EMAIL TO DATABASE ===
        email_row = {
            "user_id": request.user_id,
            "account_id": account["id"],
            "message_id": message_id,
            "subject": subject,
            "sender": from_address,
            "from_header": from_address,
            "reply_to": headers.get("reply_to", ""),
            "return_path": headers.get("return_path", ""),
            "body_html": body_html,
            "highlighted_body_html": body_html,
            "received_at": datetime.utcnow().isoformat(),
            "spf_result": auth_result["spf_result"],
            "dkim_result": auth_result["dkim_result"],
            "dmarc_policy": auth_result["dmarc_policy"],
            "auth_score": auth_result["auth_score"],
            "is_suspicious": False,
        }

        email_res = supabase.table("emails").insert(email_row).execute()
        if not email_res.data:
            return JsonResponse({'error': 'Failed to save email'}, status=500)

        email_id = email_res.data[0]["id"]

        # === INSERT AUTH RESULTS ===
        supabase.table("email_auth_results").insert({
            "email_id": email_id,
            "spf_status": auth_result["spf_result"],
            "dkim_status": auth_result["dkim_result"],
            "dmarc_status": auth_result["dmarc_policy"],
            "validation_summary": auth_result["validation_summary"],
        }).execute()

        # === URL ANALYSIS ===
        urls = extract_urls_from_html(body_html)
        url_verdicts = []
        
        for url in urls[:5]:  # Limit to 5 URLs for performance
            url_result = analyze_url(url, email_id)
            supabase.table("url_analysis").insert({
                "email_id": email_id,
                "url": url,
                "source": "body",
                "google_safebrowsing": url_result.get("google_safebrowsing"),
                "urlhaus_status": url_result.get("urlhaus_status"),
                "urlscan_status": url_result.get("urlscan_status"),
                "final_verdict": url_result.get("final_verdict"),
            }).execute()
            url_verdicts.append(url_result.get("final_verdict"))

        # === RUN DECISION ENGINE ===
        classification_result = run_rule_based_classification(email_id)

        if not classification_result:
            return JsonResponse({'error': 'Classification failed'}, status=500)

        # === RETURN RESULT ===
        response = {
            'email_id': email_id,
            'verdict': classification_result['verdict'],
            'action': classification_result['action'],
            'reason': classification_result['reason'],
            'auth_score': auth_result['auth_score'],
            'urls_analyzed': len(urls),
            'url_analysis': f"{url_verdicts.count('safe')} safe, {url_verdicts.count('suspicious')} suspicious, {url_verdicts.count('malicious')} malicious"
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
    """Get existing analysis result for an email"""
    try:
        # Get classification result
        classification = (
            supabase.table("classification_results")
            .select("*")
            .eq("email_id", email_id)
            .execute()
        )

        if not classification.data:
            return {
                'verdict': 'pending',
                'action': 'none',
                'reason': 'Analysis in progress'
            }

        result = classification.data[0]
        
        # Get email details
        email = supabase.table("emails").select("auth_score").eq("id", email_id).execute()
        auth_score = email.data[0]["auth_score"] if email.data else 0

        # Get URL analysis count
        urls = supabase.table("url_analysis").select("final_verdict").eq("email_id", email_id).execute()
        url_verdicts = [u["final_verdict"] for u in urls.data] if urls.data else []

        return {
            'email_id': email_id,
            'verdict': result.get('rule_engine_verdict', 'unknown'),
            'action': result.get('final_action', 'none'),
            'reason': 'Cached result from previous analysis',
            'auth_score': auth_score,
            'urls_analyzed': len(url_verdicts),
            'url_analysis': f"{url_verdicts.count('safe')} safe, {url_verdicts.count('suspicious')} suspicious, {url_verdicts.count('malicious')} malicious"
        }

    except Exception as e:
        logger.error(f"Error getting analysis result: {str(e)}")
        return {
            'verdict': 'error',
            'action': 'none',
            'reason': 'Failed to retrieve result'
        }


@require_http_methods(["GET"])
@require_jwt
def extension_health_check(request):
    """Health check endpoint for extension to verify backend connectivity"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': request.user_id
    })

