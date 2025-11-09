"""
Management command to fix SocialApp configuration
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Fix SocialApp configuration - remove duplicates and ensure proper site linking'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        self.stdout.write(f"Using site: {site.domain} (ID: {site.id})")
        
        # Fix Google SocialApp
        google_apps = SocialApp.objects.filter(provider='google')
        self.stdout.write(f"Found {google_apps.count()} Google SocialApp(s)")
        
        if google_apps.count() > 1:
            # Keep the first one, delete the rest
            google_app = google_apps.first()
            deleted = google_apps.exclude(pk=google_app.pk).delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} duplicate Google SocialApp(s)"))
        elif google_apps.count() == 1:
            google_app = google_apps.first()
        else:
            # Create new one
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
            )
            self.stdout.write(self.style.SUCCESS("Created new Google SocialApp"))
        
        # Update credentials
        google_app.client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        google_app.secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        google_app.save()
        
        # Ensure site is linked
        if site not in google_app.sites.all():
            google_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f"Linked Google SocialApp to site {site.id}"))
        else:
            self.stdout.write(f"Google SocialApp already linked to site {site.id}")
        
        self.stdout.write(f"Google SocialApp ID: {google_app.id}, Client ID: {google_app.client_id[:20]}...")
        
        # Fix Microsoft SocialApp
        microsoft_apps = SocialApp.objects.filter(provider='microsoft')
        self.stdout.write(f"Found {microsoft_apps.count()} Microsoft SocialApp(s)")
        
        if microsoft_apps.count() > 1:
            # Keep the first one, delete the rest
            microsoft_app = microsoft_apps.first()
            deleted = microsoft_apps.exclude(pk=microsoft_app.pk).delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} duplicate Microsoft SocialApp(s)"))
        elif microsoft_apps.count() == 1:
            microsoft_app = microsoft_apps.first()
        else:
            # Create new one
            microsoft_app = SocialApp.objects.create(
                provider='microsoft',
                name='Microsoft',
                client_id=os.getenv('MICROSOFT_CLIENT_ID', ''),
                secret=os.getenv('MICROSOFT_CLIENT_SECRET', ''),
            )
            self.stdout.write(self.style.SUCCESS("Created new Microsoft SocialApp"))
        
        # Update credentials
        microsoft_app.client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
        microsoft_app.secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
        microsoft_app.save()
        
        # Ensure site is linked
        if site not in microsoft_app.sites.all():
            microsoft_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f"Linked Microsoft SocialApp to site {site.id}"))
        else:
            self.stdout.write(f"Microsoft SocialApp already linked to site {site.id}")
        
        self.stdout.write(f"Microsoft SocialApp ID: {microsoft_app.id}, Client ID: {microsoft_app.client_id[:20]}...")
        
        self.stdout.write(self.style.SUCCESS("\nSocialApp configuration fixed successfully!"))

