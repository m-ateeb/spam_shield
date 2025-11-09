"""
Management command to set admin role for a user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Set admin role (is_staff and is_superuser) for a user by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the user to make admin')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set admin role for {email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

