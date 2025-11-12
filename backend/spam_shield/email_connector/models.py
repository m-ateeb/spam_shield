from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ConnectedAccount(models.Model):
    """Stores OAuth-connected email accounts (Gmail/Outlook)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_accounts')
    email_address = models.EmailField()
    provider = models.CharField(max_length=20, choices=[('gmail', 'Gmail'), ('outlook', 'Outlook')])
    access_token = models.TextField()  # Encrypted
    refresh_token = models.TextField(null=True, blank=True)  # Encrypted
    token_expiry = models.DateTimeField(null=True, blank=True)
    inbox_sync_status = models.CharField(max_length=20, default='connected')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'email_address']
        indexes = [
            models.Index(fields=['user', 'email_address']),
            models.Index(fields=['email_address', 'provider']),
        ]

    def __str__(self):
        return f"{self.email_address} ({self.provider})"


class Email(models.Model):
    """Stores processed email messages."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    account = models.ForeignKey(ConnectedAccount, on_delete=models.CASCADE, related_name='emails')
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    subject = models.TextField(blank=True)
    sender = models.EmailField()
    from_header = models.TextField(blank=True)
    reply_to = models.EmailField(blank=True, null=True)
    return_path = models.EmailField(blank=True, null=True)
    body_html = models.TextField(blank=True)
    highlighted_body_html = models.TextField(blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    spf_result = models.CharField(max_length=20, default='unknown')
    dkim_result = models.CharField(max_length=20, default='unknown')
    dmarc_policy = models.CharField(max_length=20, default='unknown')
    auth_score = models.IntegerField(default=0)
    is_suspicious = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True, help_text="When user opened/viewed this email")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'account']),
            models.Index(fields=['message_id']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['opened_at']),  # Index for dashboard queries
        ]

    def __str__(self):
        return f"{self.subject} from {self.sender}"


class EmailAuthResult(models.Model):
    """Stores email authentication results (SPF, DKIM, DMARC)."""
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='auth_result')
    spf_status = models.CharField(max_length=20, default='unknown')
    dkim_status = models.CharField(max_length=20, default='unknown')
    dmarc_status = models.CharField(max_length=20, default='unknown')
    validation_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Auth result for {self.email.message_id}"


class URLAnalysis(models.Model):
    """Stores URL analysis results from reputation checks."""
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='url_analyses')
    url = models.URLField(max_length=2048)
    source = models.CharField(max_length=50, default='body')  # body, subject, etc.
    google_safebrowsing = models.CharField(max_length=50, blank=True, null=True)
    urlhaus_status = models.CharField(max_length=50, blank=True, null=True)
    urlscan_status = models.CharField(max_length=50, blank=True, null=True)
    final_verdict = models.CharField(
        max_length=20,
        choices=[('safe', 'Safe'), ('suspicious', 'Suspicious'), ('malicious', 'Malicious')],
        default='safe'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'final_verdict']),
        ]

    def __str__(self):
        return f"{self.url} - {self.final_verdict}"


class ClassificationResult(models.Model):
    """Stores email classification results from decision engine."""
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='classification')
    rule_engine_verdict = models.CharField(
        max_length=20,
        choices=[
            ('safe', 'Safe'), 
            ('suspicious', 'Suspicious'), 
            ('malicious', 'Malicious'),
            ('phishing', 'Phishing')  # Added phishing as a valid verdict
        ],
        default='safe'
    )
    final_action = models.CharField(
        max_length=20,
        choices=[
            ('allow', 'Allow'), 
            ('quarantine', 'Quarantine'), 
            ('delete', 'Delete'),  # Added delete action for phishing
            ('block', 'Block')
        ],
        default='allow'
    )
    reason = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rule_engine_verdict} - {self.final_action}"


class QuarantinedEmail(models.Model):
    """Stores quarantined emails."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quarantined_emails')
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='quarantine_records')
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('released', 'Released'), ('deleted', 'Deleted')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
        unique_together = [['email', 'user']]

    def __str__(self):
        return f"Quarantined: {self.email.subject} - {self.status}"


class SystemLog(models.Model):
    """Stores system logs."""
    event_type = models.CharField(max_length=100, db_index=True)
    task_name = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.task_name}"
