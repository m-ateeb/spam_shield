"""
Management command to find and fix emails that should be classified as phishing
"""
from django.core.management.base import BaseCommand
from email_connector.models import Email, ClassificationResult, QuarantinedEmail, URLAnalysis
from spam_shield.decision_engine import run_rule_based_classification


class Command(BaseCommand):
    help = 'Find and reclassify emails that should be phishing but are not'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually fixing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find emails with malicious URLs that aren't classified as phishing
        emails_with_malicious_urls = Email.objects.filter(
            url_analyses__final_verdict='malicious'
        ).distinct()
        
        phishing_candidates = []
        
        for email in emails_with_malicious_urls:
            try:
                classification = email.classification
                verdict = classification.rule_engine_verdict.lower()
                
                # If it's not phishing but has malicious URLs, it should be
                if verdict != 'phishing' and verdict != 'malicious':
                    phishing_candidates.append(email)
            except ClassificationResult.DoesNotExist:
                # No classification - might need to classify
                phishing_candidates.append(email)
        
        # Find emails with very low auth scores that aren't phishing
        low_auth_emails = Email.objects.filter(
            auth_score__lt=20
        ).exclude(
            classification__rule_engine_verdict__in=['phishing', 'malicious']
        )
        
        for email in low_auth_emails:
            if email not in phishing_candidates:
                phishing_candidates.append(email)
        
        self.stdout.write(f'Found {len(phishing_candidates)} emails that should be phishing')
        
        if not dry_run:
            fixed_count = 0
            for email in phishing_candidates:
                try:
                    # Re-run classification
                    result = run_rule_based_classification(email.id)
                    if result and result.get('verdict') == 'phishing':
                        fixed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Fixed email {email.id}: {email.subject[:50]}')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error fixing email {email.id}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} emails')
            )
        else:
            for email in phishing_candidates[:10]:  # Show first 10
                self.stdout.write(f'Would fix: {email.id} - {email.subject[:50]}')
            if len(phishing_candidates) > 10:
                self.stdout.write(f'... and {len(phishing_candidates) - 10} more')

