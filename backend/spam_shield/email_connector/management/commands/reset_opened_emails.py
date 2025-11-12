"""
Reset opened_at for emails that shouldn't be marked as opened.
This allows users to reset stats if emails were incorrectly marked as opened.
"""
from django.core.management.base import BaseCommand
from email_connector.models import Email
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Reset opened_at for emails (useful if emails were incorrectly marked as opened)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to reset (default: all users)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without actually resetting',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.all()
        
        for user in users:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Processing user: {user.email} (ID: {user.id})')
            self.stdout.write(f'{"="*60}\n')
            
            # Count emails that would be reset
            emails_to_reset = Email.objects.filter(
                user=user,
                opened_at__isnull=False
            )
            
            count = emails_to_reset.count()
            self.stdout.write(f'Found {count} emails marked as opened')
            
            if count > 0 and not dry_run:
                # Reset opened_at
                updated = emails_to_reset.update(opened_at=None)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reset {updated} emails (opened_at set to None)')
                )
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  Dashboard stats will now show 0 until you open emails again via extension'
                    )
                )
            elif count > 0 and dry_run:
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would reset {count} emails')
                )
            else:
                self.stdout.write('No emails to reset')

