# email_connector/dashboard_views.py
# Re-export from modular structure for backward compatibility
from .views.dashboard_api_views import (
    dashboard_summary,
    admin_dashboard_summary,
    check_admin,
)
from .views.account_views import (
    list_connected_accounts,
    disconnect_account,
)

__all__ = [
    'list_connected_accounts',
    'disconnect_account',
    'dashboard_summary',
    'admin_dashboard_summary',
    'check_admin',
]
