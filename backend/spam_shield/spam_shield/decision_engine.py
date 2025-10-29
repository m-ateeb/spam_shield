# spam_shield/decision_engine.py
from email_connector.supabase_client import supabase, syslog
from datetime import datetime


def run_rule_based_classification(email_id: int):
    """
    Combine Module 2 + Module 3 results to classify email.
    Stores result into classification_results table and updates quarantine if needed.
    """
    try:
        auth_resp = (
            supabase.table("email_auth_results")
            .select("*")
            .eq("email_id", email_id)
            .execute()
        )
        auth_data = auth_resp.data[0] if auth_resp.data else None

        url_resp = (
            supabase.table("url_analysis")
            .select("final_verdict")
            .eq("email_id", email_id)
            .execute()
        )
        url_results = [u["final_verdict"] for u in url_resp.data] if url_resp.data else []

        spf = auth_data.get("spf_status", "unknown") if auth_data else "unknown"
        dkim = auth_data.get("dkim_status", "unknown") if auth_data else "unknown"
        dmarc = auth_data.get("dmarc_status", "unknown") if auth_data else "unknown"

        url_safe = url_results.count("safe")
        url_suspicious = url_results.count("suspicious")
        url_malicious = url_results.count("malicious")

        email_resp = supabase.table("emails").select("*").eq("id", email_id).execute()
        email_data = email_resp.data[0] if email_resp.data else None

        verdict = "safe"
        action = "allow"
        reason = ""

        if url_malicious > 0 or (
            sum(s in ["fail", "none", "reject", "quarantine"] for s in [spf, dkim, dmarc]) >= 2
        ):
            verdict = "phishing"
            action = "delete"
            reason = "Low authenticity score or malicious URLs"

        elif url_suspicious > 0 or (
            sum(s in ["fail", "none", "reject", "quarantine"] for s in [spf, dkim, dmarc]) == 1
        ):
            verdict = "suspicious"
            action = "quarantine"
            reason = "Suspicious email or suspicious URLs"

        else:
            verdict = "safe"
            action = "allow"
            reason = "Passed authenticity and reputation checks"

        supabase.table("classification_results").upsert(
            {
                "email_id": email_id,
                "ml_score": None,
                "rule_engine_verdict": verdict,
                "final_action": action,
                "processed_by": "rule_engine",
                "processed_at": datetime.utcnow().isoformat(),
            }
        ).execute()

        if action in ["quarantine", "delete"] and email_data:
            quarantine_email(email_data, action, reason)

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


def quarantine_email(email, action, reason):
    """Move suspicious or malicious emails into quarantine repository."""
    try:
        supabase.table("quarantined_emails").insert(
            {
                "email_id": email["id"],
                "user_id": email["user_id"],
                "reason": reason,
                "status": "pending" if action == "quarantine" else "deleted",
            }
        ).execute()

        # Mark in main emails table for frontend
        supabase.table("emails").update({"is_suspicious": True}).eq("id", email["id"]).execute()

        syslog("quarantine_add", "quarantine_email", {"email_id": email["id"], "reason": reason})
    except Exception as e:
        syslog("quarantine_error", "quarantine_email", {"email_id": email["id"], "error": str(e)})
