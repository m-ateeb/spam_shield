# email_connector/signals.py
"""
Signals for handling django-allauth OAuth events
"""
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, pre_social_login, social_account_removed
from allauth.account.signals import user_logged_in
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)


@receiver(social_account_added)
def on_social_account_added(request, sociallogin, **kwargs):
    """Called when a social account is added."""
    try:
        logger.info(f"Social account added for user: {sociallogin.user.email if sociallogin.user else 'None'}")
    except Exception as e:
        logger.error(f"Error in social_account_added signal: {e}", exc_info=True)


@receiver(pre_social_login)
def on_pre_social_login(request, sociallogin, **kwargs):
    """Called before social login - can be used to handle errors and ensure user will be logged in."""
    try:
        provider = sociallogin.account.provider if sociallogin.account else 'unknown'
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else 'no email'
        logger.info(f"Pre social login for: {provider}, email: {email}")
        
        # Check if email is available
        if not sociallogin.email_addresses:
            logger.warning(f"No email addresses found for provider: {provider}")
        
        # Ensure user will be created/logged in
        if sociallogin.user:
            logger.info(f"Social login user exists: {sociallogin.user.email}")
        else:
            logger.warning(f"No user in sociallogin for {provider}")
    except Exception as e:
        logger.error(f"Error in pre_social_login signal: {e}", exc_info=True)


@receiver(user_logged_in)
def on_user_logged_in(request, user, **kwargs):
    """Called when user logs in - ensure token exists."""
    try:
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f"User logged in via signal: {user.email}, token created: {created}")
    except Exception as e:
        logger.error(f"Error in user_logged_in signal: {e}", exc_info=True)

