from django.contrib import admin
from .models import (
    ConnectedAccount, Email, EmailAuthResult, URLAnalysis,
    ClassificationResult, QuarantinedEmail, SystemLog
)


@admin.register(ConnectedAccount)
class ConnectedAccountAdmin(admin.ModelAdmin):
    list_display = ['email_address', 'provider', 'user', 'inbox_sync_status', 'created_at']
    list_filter = ['provider', 'inbox_sync_status']
    search_fields = ['email_address', 'user__email']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'account', 'is_suspicious', 'auth_score', 'received_at']
    list_filter = ['is_suspicious', 'spf_result', 'dkim_result']
    search_fields = ['subject', 'sender', 'message_id']


@admin.register(EmailAuthResult)
class EmailAuthResultAdmin(admin.ModelAdmin):
    list_display = ['email', 'spf_status', 'dkim_status', 'dmarc_status']


@admin.register(URLAnalysis)
class URLAnalysisAdmin(admin.ModelAdmin):
    list_display = ['url', 'email', 'final_verdict', 'source']
    list_filter = ['final_verdict', 'source']


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    list_display = ['email', 'rule_engine_verdict', 'final_action', 'confidence_score']


@admin.register(QuarantinedEmail)
class QuarantinedEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'status', 'created_at']
    list_filter = ['status']


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'task_name', 'created_at']
    list_filter = ['event_type']
    readonly_fields = ['created_at']
