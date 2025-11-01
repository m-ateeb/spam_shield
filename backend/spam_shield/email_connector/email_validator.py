# email_connector/email_validator.py
import dkim
import dns.resolver
import re
from dmarc import DMARC
from email_connector.supabase_client import syslog

def validate_email_authenticity(raw_email: bytes, sender_domain: str, message_id: str = None):
    """
    Validate SPF, DKIM, and DMARC authenticity for a given email.
    Returns a dict with individual results + overall score.
    """
    results = {
        "spf_result": "unknown",
        "dkim_result": "unknown",
        "dmarc_policy": "unknown",
        "auth_score": 0,
        "validation_summary": ""
    }

    # === SPF CHECK ===
    try:
        txt_records = dns.resolver.resolve(sender_domain, "TXT")
        spf_record = any("v=spf1" in r.to_text() for r in txt_records)
        results["spf_result"] = "pass" if spf_record else "fail"
    except Exception as e:
        results["spf_result"] = "fail"
        syslog("spf_error", "validate_email_authenticity", {"domain": sender_domain, "error": str(e)})

    # === DKIM CHECK ===
    try:
        dkim_result = dkim.verify(raw_email)
        results["dkim_result"] = "pass" if dkim_result else "fail"
    except Exception as e:
        results["dkim_result"] = "fail"
        syslog("dkim_error", "validate_email_authenticity", {"message_id": message_id, "error": str(e)})

    # === DMARC CHECK ===
    try:
        dmarc_record = dns.resolver.resolve(f"_dmarc.{sender_domain}", "TXT")
        dmarc_txt = next((r.to_text() for r in dmarc_record if "v=DMARC1" in r.to_text()), None)
        if dmarc_txt:
            policy = re.search(r"p=([^;]+)", dmarc_txt)
            results["dmarc_policy"] = policy.group(1) if policy else "none"
        else:
            results["dmarc_policy"] = "none"
    except Exception as e:
        results["dmarc_policy"] = "none"
        syslog("dmarc_error", "validate_email_authenticity", {"domain": sender_domain, "error": str(e)})

    # === SCORE CALCULATION ===
    score_map = {"pass": 33, "fail": 0, "none": 10, "quarantine": 15, "reject": 20}
    score = (
        score_map.get(results["spf_result"], 0) +
        score_map.get(results["dkim_result"], 0) +
        score_map.get(results["dmarc_policy"], 0)
    )
    results["auth_score"] = score
    results["validation_summary"] = (
        f"SPF={results['spf_result']}, DKIM={results['dkim_result']}, "
        f"DMARC={results['dmarc_policy']}, SCORE={score}"
    )

    return results
