from django.contrib import admin
from django.urls import path, include
from email_connector import views, dashboard_views, extension_views, auth_views, admin_views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # IMPORTANT: Override django-allauth callback views BEFORE including allauth.urls
    # This ensures our custom callbacks take precedence
    path('accounts/google/login/callback/', auth_views.google_oauth_callback, name='google_callback'),
    path('accounts/microsoft/login/callback/', auth_views.microsoft_oauth_callback, name='microsoft_callback'),
    
    # Custom logout endpoint (CSRF exempt for token auth)
    path('accounts/logout/', auth_views.logout_view, name='logout'),
    
    # Django Allauth URLs for user authentication (Google/Microsoft OAuth login)
    # This must come AFTER our custom callback overrides
    path('accounts/', include('allauth.urls')),
    
    # User authentication endpoints
    path('api/auth/google/', auth_views.google_oauth_login, name='google_oauth_login'),
    path('api/auth/microsoft/', auth_views.microsoft_oauth_login, name='microsoft_oauth_login'),
    path('api/auth/login/', auth_views.email_password_login, name='email_password_login'),
    path('api/auth/signup/', auth_views.email_password_signup, name='email_password_signup'),
    path('api/auth/token/', auth_views.get_auth_token, name='get_auth_token'),
    path('api/auth/user/', auth_views.user_info, name='user_info'),
    path('api/auth/callback/', auth_views.oauth_callback, name='oauth_callback'),
    
    # Email account OAuth (for connecting Gmail/Outlook accounts)
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
    path('api/accounts/disconnect/', dashboard_views.disconnect_account),
    path('api/dashboard/summary/', dashboard_views.dashboard_summary),
    path('api/dashboard/admin/summary/', dashboard_views.admin_dashboard_summary),
    path('api/auth/admin/check/', dashboard_views.check_admin),
    
    # Admin APIs
    path('api/admin/users/', admin_views.admin_users_list),
    path('api/admin/users/update/', admin_views.admin_user_update),
    path('api/admin/reports/', admin_views.admin_reports_summary),
    path('api/admin/rules/', admin_views.admin_rules_config),
    path('api/admin/rules/update/', admin_views.admin_rules_update),

    # Extension APIs (with and without trailing slash for compatibility)
    path('api/extension/analyze/', extension_views.analyze_email_extension),
    path('api/extension/analyze', extension_views.analyze_email_extension),  # Fallback without slash
    path('api/extension/health/', extension_views.extension_health_check),
    path('api/extension/health', extension_views.extension_health_check),  # Fallback without slash
]
