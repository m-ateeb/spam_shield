# email_connector/dashboard_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from email_connector.supabase_client import supabase
from email_connector.auth_utils import require_jwt

@require_GET
@require_jwt
def list_connected_accounts(request):
    """List all connected email accounts for logged-in user."""
    try:
        res = (
            supabase.table("connected_accounts")
            .select("id, email_address, provider, inbox_sync_status, token_expiry")
            .eq("user_id", request.user_id)
            .execute()
        )
        return JsonResponse({"accounts": res.data or []})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_GET
@require_jwt
def dashboard_summary(request):
    """Summarize stats for selected email account."""
    email = request.GET.get("email")
    if not email:
        return JsonResponse({"error": "Missing email"}, status=400)

    try:
        acc = (
            supabase.table("connected_accounts")
            .select("id")
            .eq("email_address", email)
            .eq("user_id", request.user_id)
            .execute()
        )
        if not acc.data:
            return JsonResponse({"error": "Account not found"}, status=404)

        account_id = acc.data[0]["id"]

        emails = supabase.table("emails").select("id, is_suspicious").eq("account_id", account_id).execute()
        total_emails = len(emails.data or [])
        suspicious = sum(1 for e in emails.data if e["is_suspicious"])

        quarantine = (
            supabase.table("quarantined_emails")
            .select("id, status")
            .eq("user_id", request.user_id)
            .execute()
        )
        quarantined = len([q for q in quarantine.data if q["status"] == "pending"])

        return JsonResponse({
            "account_email": email,
            "total_emails": total_emails,
            "suspicious_emails": suspicious,
            "quarantined_emails": quarantined,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
