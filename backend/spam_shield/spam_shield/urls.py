from django.contrib import admin
from django.urls import path
from email_connector import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Google OAuth
    path('oauth/google/', views.google_login),
    path('oauth/google/callback/', views.google_callback),

    # Gmail operations
    path('gmail/fetch/', views.fetch_recent_gmail),
    path('webhook/gmail/', views.gmail_webhook),

    # Microsoft OAuth
    path('oauth/microsoft/', views.microsoft_login),
    path('oauth/microsoft/callback/', views.microsoft_callback),
    path('webhook/outlook/', views.outlook_webhook),

    # Quarantine API (Module 5)
    path('api/quarantine/list/', views.list_quarantined_emails),
    path('api/quarantine/release/', views.release_quarantined_email),
    path('api/quarantine/delete/', views.delete_quarantined_email),
]
