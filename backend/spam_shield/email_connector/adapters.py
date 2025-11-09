# email_connector/adapters.py
"""
Custom django-allauth adapters to handle OAuth callbacks
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
import logging

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle OAuth errors and redirect to frontend."""
    
    def get_app(self, request, provider, client_id=None):
        """Override to handle MultipleObjectsReturned error and ensure app is found."""
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.shortcuts import get_current_site
        from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
        
        site = get_current_site(request)
        
        try:
            # Try the parent method first
            return super().get_app(request, provider, client_id)
        except MultipleObjectsReturned:
            # Handle duplicates - check if there actually are multiple apps
            all_apps = SocialApp.objects.filter(provider=provider)
            app_count = all_apps.count()
            
            # Get the first one linked to this site
            apps = SocialApp.objects.filter(provider=provider, sites=site)
            if apps.exists():
                app = apps.first()
                # If there are multiple apps, clean up duplicates (keep only this one)
                if app_count > 1:
                    logger.warning(f"Multiple SocialApp objects found for {provider} ({app_count} total), cleaning up duplicates.")
                    # Delete all other apps for this provider
                    SocialApp.objects.filter(provider=provider).exclude(pk=app.pk).delete()
                    logger.info(f"Cleaned up duplicate SocialApp objects for {provider}, keeping app ID {app.id}.")
                return app
            # If none linked to site, get any and link it
            if all_apps.exists():
                app = all_apps.first()
                # Clean up duplicates if there are multiple
                if app_count > 1:
                    logger.warning(f"Multiple SocialApp objects found for {provider} ({app_count} total), cleaning up duplicates.")
                    SocialApp.objects.filter(provider=provider).exclude(pk=app.pk).delete()
                    logger.info(f"Cleaned up duplicate SocialApp objects for {provider}, keeping app ID {app.id}.")
                if site not in app.sites.all():
                    app.sites.add(site)
                    logger.info(f"Linked SocialApp {app.id} for {provider} to site {site.id}.")
                return app
            raise ObjectDoesNotExist(f"No SocialApp found for provider {provider}")
        except ObjectDoesNotExist:
            # Try to find any app for this provider and link it to the site
            apps = SocialApp.objects.filter(provider=provider)
            if apps.exists():
                app = apps.first()
                if site not in app.sites.all():
                    app.sites.add(site)
                    logger.info(f"Found and linked SocialApp {app.id} for {provider} to site {site.id}.")
                return app
            logger.error(f"No SocialApp found for provider {provider} in database.")
            raise
        except Exception as e:
            # For any other error, try to find the app anyway
            logger.warning(f"Error in get_app for {provider}: {e}, attempting fallback lookup.")
            apps = SocialApp.objects.filter(provider=provider)
            if apps.exists():
                app = apps.first()
                if site not in app.sites.all():
                    app.sites.add(site)
                logger.info(f"Fallback: Found SocialApp {app.id} for {provider} and linked to site.")
                return app
            raise
    
    def pre_social_login(self, request, sociallogin):
        """Called before social login is processed."""
        # Allow the login to proceed
        pass
    
    def on_authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors - log but don't interfere."""
        # Only log if there's an actual error or exception
        # "unknown" errors without exceptions are often false alarms when the flow actually succeeds
        if exception:
            logger.error(f"OAuth authentication error: {error}, exception: {exception}, provider: {provider_id}")
            logger.error(f"Exception details: {type(exception).__name__}: {str(exception)}", exc_info=True)
            import traceback
            logger.error(f"Exception traceback: {traceback.format_exc()}")
        elif error and error != 'unknown':
            # Only log if error is not "unknown" (which is often a false alarm)
            logger.error(f"OAuth authentication error: {error}, provider: {provider_id}")
            if hasattr(request, 'GET'):
                logger.error(f"Request GET params: {dict(request.GET)}")
        else:
            # "unknown" error without exception - likely a false alarm, log as warning
            logger.debug(f"OAuth authentication warning (likely false alarm): {error}, provider: {provider_id}")
        
        # Return None to let django-allauth handle the error
        # The callback view will catch and redirect properly
        return None
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors (deprecated, kept for compatibility)."""
        return self.on_authentication_error(request, provider_id, error, exception, extra_context)
    
    def is_open_for_signup(self, request, sociallogin):
        """Allow automatic signup for OAuth users."""
        return True
    
    def save_user(self, request, sociallogin, form=None):
        """Save the user from social login - django-allauth will log them in."""
        user = super().save_user(request, sociallogin, form)
        logger.info(f"User saved from OAuth: {user.email if user else 'None'}")
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect after connecting a social account."""
        return '/api/auth/callback/'
    
    def get_login_redirect_url(self, request):
        """Override login redirect to use our custom callback."""
        # Check if we have a frontend redirect in session (from OAuth)
        frontend_url = request.session.get('frontend_redirect')
        if frontend_url:
            # User will be redirected to our custom callback which handles token creation
            return '/api/auth/callback/'
        # Default redirect
        return super().get_login_redirect_url(request)
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data from social account."""
        try:
            user = super().populate_user(request, sociallogin, data)
            # Ensure email is set
            if not user.email:
                # Try to get email from data or email_addresses
                email = data.get('email') or (sociallogin.email_addresses[0].email if sociallogin.email_addresses else None)
                if email:
                    user.email = email
                else:
                    logger.warning(f"No email found for OAuth user from {sociallogin.account.provider if sociallogin.account else 'unknown'}")
            # Set username if not set
            if not user.username:
                user.username = user.email or data.get('id', '') or data.get('sub', '')
            logger.info(f"Populated user: {user.email if user else 'None'}, username: {user.username if user else 'None'}")
            return user
        except Exception as e:
            logger.error(f"Error populating user: {e}", exc_info=True)
            raise


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to handle login redirects."""
    
    def get_login_redirect_url(self, request):
        """Redirect to our custom callback after login."""
        return '/api/auth/callback/'

