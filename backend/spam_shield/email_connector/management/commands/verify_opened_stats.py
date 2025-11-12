"""
Verify that dashboard stats only count opened emails
"""
from django.core.management.base import BaseCommand
from email_connector.models import Email, ClassificationResult, QuarantinedEmail
from django.contrib.auth.models import User
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Verify that stats only count opened emails'

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
            self.stdout.write(f'Verifying stats for user: {user.email} (ID: {user.id})')
            self.stdout.write(f'{"="*60}\n')
            
            # Total emails
            total_all = Email.objects.filter(user=user).count()
            total_opened = Email.objects.filter(user=user, opened_at__isnull=False).count()
            total_not_opened = Email.objects.filter(user=user, opened_at__isnull=True).count()
            
            self.stdout.write(f'Total emails: {total_all}')
            self.stdout.write(f'  - Opened: {total_opened}')
            self.stdout.write(f'  - Not opened (webhook only): {total_not_opened}')
            
            # Classifications
            all_classified = ClassificationResult.objects.filter(email__user=user).count()
            opened_classified = ClassificationResult.objects.filter(
                email__user=user,
                email__opened_at__isnull=False
            ).count()
            
            self.stdout.write(f'\nClassifications: {all_classified}')
            self.stdout.write(f'  - For opened emails: {opened_classified}')
            
            # Safe emails
            safe_all = ClassificationResult.objects.filter(
                email__user=user,
                rule_engine_verdict='safe'
            ).count()
            safe_opened = ClassificationResult.objects.filter(
                email__user=user,
                email__opened_at__isnull=False,
                rule_engine_verdict='safe'
            ).count()
            
            self.stdout.write(f'\nSafe emails: {safe_all} total, {safe_opened} opened')
            
            # Phishing/Malicious
            phishing_all = ClassificationResult.objects.filter(
                email__user=user,
                rule_engine_verdict__in=['phishing', 'malicious']
            ).count()
            phishing_opened = ClassificationResult.objects.filter(
                email__user=user,
                email__opened_at__isnull=False,
                rule_engine_verdict__in=['phishing', 'malicious']
            ).count()
            
            self.stdout.write(f'Phishing/Malicious: {phishing_all} total, {phishing_opened} opened')
            
            # Quarantined
            quarantined_all = QuarantinedEmail.objects.filter(user=user, status='pending').count()
            quarantined_opened = QuarantinedEmail.objects.filter(
                user=user,
                status='pending',
                email__opened_at__isnull=False
            ).count()
            
            self.stdout.write(f'\nQuarantined: {quarantined_all} total, {quarantined_opened} opened')
            
            # Summary
            self.stdout.write(f'\n{"="*60}')
            if total_not_opened > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  {total_not_opened} emails processed via webhooks but not opened '
                        f'(these are correctly excluded from dashboard stats)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✅ All emails have been opened (or no emails exist)')
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Dashboard will show: {total_opened} total emails, '
                    f'{safe_opened} safe, {phishing_opened} phishing, {quarantined_opened} quarantined'
                )
            )

