from django.apps import AppConfig


class EmailConnectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_connector'

    def ready(self):
        # Import signals
        import email_connector.signals  # noqa
        
        # Set Site domain for django-allauth after migrations
        try:
            from django.contrib.sites.models import Site
            site = Site.objects.get(id=1)
            if site.domain != 'localhost:8000':
                site.domain = 'localhost:8000'
                site.name = 'SpamShield'
                site.save()
        except Exception:
            pass  # Site will be created during migration
        
        # Ensure SocialApp exists for Google and Microsoft
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
            import os
            
            site = Site.objects.get(id=1)
            
            # Handle Google SocialApp - remove duplicates first
            google_apps = SocialApp.objects.filter(provider='google')
            if google_apps.count() > 1:
                # Keep the first one, delete the rest
                google_app = google_apps.first()
                google_apps.exclude(pk=google_app.pk).delete()
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
            
            # Update credentials
            google_app.client_id = os.getenv('GOOGLE_CLIENT_ID', '')
            google_app.secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
            google_app.save()
            
            # Add site to SocialApp if not already added
            if site not in google_app.sites.all():
                google_app.sites.add(site)
            
            # Handle Microsoft SocialApp - remove duplicates first
            microsoft_apps = SocialApp.objects.filter(provider='microsoft')
            if microsoft_apps.count() > 1:
                # Keep the first one, delete the rest
                microsoft_app = microsoft_apps.first()
                microsoft_apps.exclude(pk=microsoft_app.pk).delete()
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
            
            # Update credentials
            microsoft_app.client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
            microsoft_app.secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
            microsoft_app.save()
            
            # Add site to SocialApp if not already added
            if site not in microsoft_app.sites.all():
                microsoft_app.sites.add(site)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not auto-create SocialApp: {e}. Please create manually in Django admin.")