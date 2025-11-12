"""
Fix emails that should be quarantined but aren't
"""
from django.core.management.base import BaseCommand
from email_connector.models import Email, ClassificationResult, QuarantinedEmail
from spam_shield.decision_engine import quarantine_email
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Quarantine emails that should be quarantined but are missing from quarantine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to fix (default: all users)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually fixing it',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.all()
        
        total_fixed = 0
        
        for user in users:
            self.stdout.write(f'\nChecking user: {user.email} (ID: {user.id})')
            
            # Find emails that should be quarantined but aren't
            suspicious_emails = Email.objects.filter(
                user=user,
                classification__rule_engine_verdict__in=['suspicious', 'phishing', 'malicious']
            )
            
            missing_quarantine = []
            for email in suspicious_emails:
                if not QuarantinedEmail.objects.filter(email=email, user=user).exists():
                    missing_quarantine.append(email)
            
            if not missing_quarantine:
                self.stdout.write(f'  ✅ All suspicious emails are already quarantined')
                continue
            
            self.stdout.write(
                self.style.WARNING(
                    f'  Found {len(missing_quarantine)} emails that should be quarantined'
                )
            )
            
            if not dry_run:
                fixed_count = 0
                for email in missing_quarantine:
                    try:
                        classification = email.classification
                        action = classification.final_action
                        reason = classification.reason or f"Classified as {classification.rule_engine_verdict}"
                        
                        # Quarantine the email
                        quarantine_email(email, action, reason)
                        fixed_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Quarantined email {email.id}: {email.subject[:50]} '
                                f'({classification.rule_engine_verdict})'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Error quarantining email {email.id}: {str(e)}'
                            )
                        )
                
                total_fixed += fixed_count
                self.stdout.write(
                    self.style.SUCCESS(f'  Fixed {fixed_count} emails for user {user.email}')
                )
            else:
                for email in missing_quarantine[:10]:
                    try:
                        classification = email.classification
                        self.stdout.write(
                            f'  Would quarantine: Email {email.id} - {email.subject[:50]} '
                            f'({classification.rule_engine_verdict})'
                        )
                    except:
                        self.stdout.write(f'  Would quarantine: Email {email.id} - {email.subject[:50]}')
                
                if len(missing_quarantine) > 10:
                    self.stdout.write(f'  ... and {len(missing_quarantine) - 10} more')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Total fixed: {total_fixed} emails')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nRun without --dry-run to apply fixes')
            )

