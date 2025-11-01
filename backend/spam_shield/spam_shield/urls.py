from django.contrib import admin
from django.urls import path
from email_connector import views, dashboard_views, extension_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # OAuth
    path('oauth/google/', views.google_login),
    path('oauth/google/callback/', views.google_callback),
    path('oauth/microsoft/', views.microsoft_login),
    path('oauth/microsoft/callback/', views.microsoft_callback),

    # Webhooks
    path('webhook/gmail/', views.gmail_webhook),
    path('webhook/outlook/', views.outlook_webhook),

    # Quarantine APIs
    path('api/quarantine/list/', views.list_quarantined_emails),
    path('api/quarantine/release/', views.release_quarantined_email),
    path('api/quarantine/delete/', views.delete_quarantined_email),

    # Dashboard APIs
    path('api/accounts/', dashboard_views.list_connected_accounts),
    path('api/dashboard/summary/', dashboard_views.dashboard_summary),

    # Extension APIs
    path('api/extension/analyze', extension_views.analyze_email_extension),
    path('api/extension/health', extension_views.extension_health_check),
]
