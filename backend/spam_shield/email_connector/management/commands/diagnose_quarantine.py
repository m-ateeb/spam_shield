"""
Diagnostic command to check why emails aren't showing in quarantine
"""
from django.core.management.base import BaseCommand
from email_connector.models import (
    Email, ClassificationResult, QuarantinedEmail, 
    URLAnalysis, EmailAuthResult
)
from django.contrib.auth.models import User
from django.db.models import Count


class Command(BaseCommand):
    help = 'Diagnose why emails are not showing in quarantine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to check (default: all users)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Checking user: {user.email} (ID: {user.id})')
            self.stdout.write(f'{"="*60}\n')
            
            # Total emails
            total_emails = Email.objects.filter(user=user).count()
            self.stdout.write(f'Total emails: {total_emails}')
            
            # Emails with classification
            emails_with_classification = Email.objects.filter(
                user=user,
                classification__isnull=False
            ).count()
            self.stdout.write(f'Emails with classification: {emails_with_classification}')
            
            # Classification breakdown
            classifications = ClassificationResult.objects.filter(email__user=user)
            self.stdout.write(f'\nClassification breakdown:')
            for item in classifications.values('rule_engine_verdict').annotate(
                count=Count('id')
            ):
                self.stdout.write(f'  {item["rule_engine_verdict"]}: {item["count"]}')
            
            # Quarantined emails
            quarantined = QuarantinedEmail.objects.filter(user=user)
            total_quarantined = quarantined.count()
            self.stdout.write(f'\nTotal quarantined entries: {total_quarantined}')
            
            # Quarantined by status
            for item in quarantined.values('status').annotate(
                count=Count('id')
            ):
                self.stdout.write(f'  Status {item["status"]}: {item["count"]}')
            
            # Emails that should be quarantined but aren't
            suspicious_emails = Email.objects.filter(
                user=user,
                classification__rule_engine_verdict__in=['suspicious', 'phishing', 'malicious']
            )
            self.stdout.write(f'\nEmails classified as suspicious/phishing/malicious: {suspicious_emails.count()}')
            
            # Check which ones are missing from quarantine
            missing_quarantine = []
            for email in suspicious_emails:
                if not QuarantinedEmail.objects.filter(email=email, user=user).exists():
                    missing_quarantine.append(email)
            
            if missing_quarantine:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  Found {len(missing_quarantine)} emails that should be quarantined but are NOT:'
                    )
                )
                for email in missing_quarantine[:10]:  # Show first 10
                    try:
                        classification = email.classification
                        self.stdout.write(
                            f'  - Email ID {email.id}: {email.subject[:50]} '
                            f'(Verdict: {classification.rule_engine_verdict}, '
                            f'Action: {classification.final_action})'
                        )
                    except:
                        self.stdout.write(f'  - Email ID {email.id}: {email.subject[:50]} (No classification)')
                
                if len(missing_quarantine) > 10:
                    self.stdout.write(f'  ... and {len(missing_quarantine) - 10} more')
            
            # Check emails in quarantine but missing classification
            quarantined_no_classification = []
            for q in quarantined:
                try:
                    q.email.classification
                except:
                    quarantined_no_classification.append(q)
            
            if quarantined_no_classification:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️  Found {len(quarantined_no_classification)} quarantined emails WITHOUT classification:'
                    )
                )
                for q in quarantined_no_classification[:10]:
                    self.stdout.write(
                        f'  - Quarantine ID {q.id}: Email ID {q.email.id} '
                        f'({q.email.subject[:50] if q.email.subject else "No subject"})'
                    )
            
            # Check emails with pending URL analysis
            emails_pending_urls = Email.objects.filter(
                user=user,
                url_analyses__final_verdict='pending'
            ).distinct().count()
            self.stdout.write(f'\nEmails with pending URL analysis: {emails_pending_urls}')
            
            # Check emails without auth results
            emails_no_auth = Email.objects.filter(
                user=user
            ).exclude(
                auth_result__isnull=False
            ).count()
            self.stdout.write(f'Emails without auth results: {emails_no_auth}')
            
            # Summary
            self.stdout.write(f'\n{"="*60}')
            if missing_quarantine:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ ISSUE FOUND: {len(missing_quarantine)} emails should be quarantined but are not!'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'Run: python manage.py fix_quarantine_missing to fix this'
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS('✅ All suspicious emails are quarantined'))
            
            if quarantined_no_classification:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  {len(quarantined_no_classification)} quarantined emails lack classification '
                        f'(they will not show in the list)'
                    )
                )

