# Spam Shield - Complete Project Structure Documentation

## Overview
Spam Shield is a comprehensive anti-spam email protection system with three main components:
- **Frontend**: React + TypeScript web application
- **Backend**: Django REST API with email processing
- **Extension**: Browser extension for Gmail/Outlook integration

---

## 📁 Frontend Structure (`frontend/`)

### Core Application Files
- **`src/main.tsx`**: Application entry point, renders App component
- **`src/App.tsx`**: Main application component with routing configuration
- **`src/index.css`**: Global styles and Tailwind CSS imports
- **`src/App.css`**: Application-specific styles

### Configuration Files
- **`vite.config.ts`**: Vite build configuration
- **`tsconfig.json`**: TypeScript configuration
- **`tailwind.config.ts`**: Tailwind CSS configuration
- **`package.json`**: Node.js dependencies and scripts
- **`postcss.config.js`**: PostCSS configuration for CSS processing

### Routes (`src/routes/`)
- **`ProtectedRoutes.tsx`**: Route wrapper for authenticated routes
- **`AdminRoute.tsx`**: Route wrapper for admin-only routes

### Context (`src/context/`)
- **`AuthContext.tsx`**: Authentication context provider managing user state, login, logout, token management

### Hooks (`src/hooks/`)
- **`use-mobile.tsx`**: Hook to detect mobile devices
- **`use-toast.ts`**: Toast notification hook
- **`useDashboard.ts`**: Reusable hook for dashboard data fetching with auto-refresh

### Libraries (`src/lib/`)
- **`api.ts`**: Axios API client with authentication interceptors
- **`utils.ts`**: Utility functions (cn for className merging, etc.)
- **`extensionAuth.ts`**: Extension authentication utilities
- **`extensionSync.ts`**: Extension synchronization utilities

### Components (`src/components/`)

#### Layout Components
- **`DashboardLayout.tsx`**: Main dashboard layout wrapper with sidebar
- **`Header.tsx`**: Application header with navigation
- **`Footer.tsx`**: Application footer (uses modular footer components)

#### Footer Components (`footer/`)
- **`FooterBrand.tsx`**: Footer brand section with logo and social links
- **`FooterSection.tsx`**: Reusable footer section wrapper
- **`FooterLink.tsx`**: Footer link component (supports both router and external links)

#### Dashboard Components (`dashboard/`)
- **`DashboardHeader.tsx`**: Reusable dashboard header with title, subtitle, and action button
- **`DashboardLoading.tsx`**: Loading state component for dashboards
- **`DashboardError.tsx`**: Error state component for dashboards
- **`ManagementCard.tsx`**: Reusable management card for admin dashboard

#### Quarantine Components (`quarantine/`)
- **`QuarantineTable.tsx`**: Main quarantine table component
- **`QuarantineHeader.tsx`**: Quarantine table header with refresh button
- **`QuarantineTableRow.tsx`**: Individual quarantine email row component
- **`types.ts`**: TypeScript interfaces for quarantine data
- **`utils.ts`**: Utility functions (threat color mapping)
- **`hooks/useQuarantine.ts`**: Hook for fetching quarantine data
- **`hooks/useQuarantineActions.ts`**: Hook for quarantine actions (release/delete)

#### UI Components (`ui/`)
- **`sidebar/`**: Modular sidebar component system
  - `constants.ts`: Sidebar constants (widths, cookie names, etc.)
  - `types.ts`: TypeScript types for sidebar
  - `context.tsx`: Sidebar context and provider
  - `sidebar.tsx`: Main sidebar component
  - `sidebar-trigger.tsx`: Sidebar toggle button
  - `sidebar-rail.tsx`: Sidebar drag handle
  - `sidebar-inset.tsx`: Main content area wrapper
  - `sidebar-parts.tsx`: Header, footer, content, separator, input components
  - `sidebar-group.tsx`: Group components for organizing sidebar items
  - `sidebar-menu.tsx`: Menu components (menu, item, button, action, badge, skeleton, sub-menu)
  - `index.ts`: Public exports

- **`chart/`**: Chart component system
  - `types.ts`: Chart configuration types
  - `context.tsx`: Chart context provider
  - `chart-container.tsx`: Main chart container component
  - `chart-style.tsx`: Dynamic chart styling component
  - `chart-tooltip.tsx`: Chart tooltip components
  - `chart-legend.tsx`: Chart legend components
  - `utils.ts`: Chart utility functions
  - `index.ts`: Public exports

- **Other UI components**: Button, Card, Input, Label, Table, Badge, Sheet, Skeleton, Tooltip, etc. (shadcn/ui components)

#### Auth Components (`auth/`)
- **`Login.tsx`**: User login page
- **`Signup.tsx`**: User registration page
- **`Logout.tsx`**: Logout handler component
- **`LogoutButton.tsx`**: Logout button component
- **`ProtectedRoute.tsx`**: Route wrapper for protected pages
- **`PublicRoute.tsx`**: Route wrapper for public pages (redirects if authenticated)

#### Other Components
- **`StatCard.tsx`**: Statistics card component for dashboards
- **`ActivityChart.tsx`**: Activity chart component
- **`ThemeProvider.tsx`**: Theme context provider (dark/light mode)

### Pages (`src/pages/`)

#### Dashboard Pages (`dashboard/`)
- **`UserDashboard.tsx`**: User dashboard with stats, charts, and quarantine preview
- **`AdminDashboard.tsx`**: Admin dashboard with system stats and management cards

#### Admin Pages (`admin/`)
- **`AdminUsers.tsx`**: User management page
- **`AdminRules.tsx`**: Spam rules configuration (uses modular structure)
  - `rules/AdminRules.tsx`: Main rules page
  - `rules/types.ts`: Rules configuration types
  - `rules/hooks/useRules.ts`: Hook for fetching rules
  - `rules/hooks/useRulesActions.ts`: Hook for saving rules
  - `rules/components/RuleSection.tsx`: Reusable rule section component
- **`AdminReports.tsx`**: System reports page
- **`AdminSettings.tsx`**: System settings page

#### Landing Pages (`landingpages/`)
- **`Home.tsx`**: Landing page
- **`Features.tsx`**: Features page
- **`About.tsx`**: About page
- **`Pricing.tsx`**: Pricing page
- **`Contact.tsx`**: Contact page

#### Other Pages
- **`Settings.tsx`**: User settings page
- **`Quarantine.tsx`**: Full quarantine management page
- **`NotFound.tsx`**: 404 error page

---

## 📁 Backend Structure (`backend/spam_shield/`)

### Django Project Configuration (`spam_shield/`)
- **`settings.py`**: Django settings (database, installed apps, middleware, etc.)
- **`urls.py`**: Main URL routing configuration
- **`wsgi.py`**: WSGI application entry point
- **`asgi.py`**: ASGI application entry point
- **`celery.py`**: Celery configuration for async tasks
- **`authentication.py`**: Custom authentication backends
- **`tasks.py`**: Celery tasks for async email processing
- **`decision_engine.py`**: Main decision engine entry point (delegates to classification module)

### Classification Module (`spam_shield/classification/`)
- **`rules.py`**: Classification rules and thresholds
  - `KNOWN_LEGITIMATE_DOMAINS`: List of trusted domains
  - `count_auth_results()`: Count SPF/DKIM/DMARC results
  - `count_url_results()`: Count URL analysis results
  - `is_known_legitimate_domain()`: Check if domain is trusted
  - `classify_by_malicious_urls()`: Classify based on malicious URLs
  - `classify_by_auth_score()`: Classify based on authentication score

- **`classifier.py`**: Main classification logic
  - `get_email_data()`: Fetch email and related data
  - `check_url_analysis_complete()`: Verify URL analysis is complete
  - `calculate_classification()`: Calculate email classification
  - `save_classification_result()`: Save classification to database
  - `handle_quarantine()`: Handle email quarantine actions

- **`__init__.py`**: Module exports

### Email Connector App (`email_connector/`)

#### Models (`models.py`)
- **`ConnectedAccount`**: OAuth-connected email accounts (Gmail/Outlook)
- **`Email`**: Processed email messages
- **`EmailAuthResult`**: SPF/DKIM/DMARC authentication results
- **`URLAnalysis`**: URL reputation analysis results
- **`ClassificationResult`**: Email classification results
- **`QuarantinedEmail`**: Quarantined emails
- **`SystemLog`**: System event logs

#### Services (`services/`)
- **`oauth_service.py`**: OAuth authentication service
  - `authenticate_user()`: Authenticate user from token/session
  - `build_redirect_uri()`: Build OAuth redirect URI
  - `get_google_auth_url()`: Build Google OAuth URL
  - `get_microsoft_auth_url()`: Build Microsoft OAuth URL
  - `exchange_google_code()`: Exchange Google OAuth code for tokens
  - `exchange_microsoft_code()`: Exchange Microsoft OAuth code for tokens
  - `get_google_user_info()`: Get Google user information
  - `get_microsoft_user_info()`: Get Microsoft user information

- **`auth_service.py`**: Authentication service
  - `create_user()`: Create new user account
  - `authenticate_user()`: Authenticate user by email/password
  - `get_or_create_token()`: Get or create API token
  - `get_user_info()`: Get user information

- **`dashboard_service.py`**: Dashboard statistics service
  - `get_user_summary()`: Get user dashboard statistics
  - `get_admin_summary()`: Get admin dashboard statistics

- **`quarantine_service.py`**: Quarantine management service
  - `list_quarantined_emails()`: List quarantined emails
  - `release_email()`: Release quarantined email
  - `delete_email()`: Delete quarantined email

- **`__init__.py`**: Service exports

#### Views (`views/`)
- **`oauth_views.py`**: OAuth views for email account connection
  - `google_login()`: Redirect to Google OAuth
  - `google_callback()`: Handle Google OAuth callback
  - `microsoft_login()`: Redirect to Microsoft OAuth
  - `microsoft_callback()`: Handle Microsoft OAuth callback

- **`auth_oauth_views.py`**: OAuth views for user authentication
  - `google_oauth_login()`: Redirect to Google OAuth for login
  - `microsoft_oauth_login()`: Redirect to Microsoft OAuth for login

- **`auth_api_views.py`**: Authentication API views
  - `get_auth_token()`: Get or create API token
  - `email_password_login()`: Login with email/password
  - `email_password_signup()`: Sign up with email/password
  - `logout_view()`: Logout user
  - `user_info()`: Get current user information

- **`dashboard_api_views.py`**: Dashboard API views
  - `dashboard_summary()`: Get user dashboard summary
  - `admin_dashboard_summary()`: Get admin dashboard summary
  - `check_admin()`: Check if user is admin

- **`account_views.py`**: Account management views
  - `list_connected_accounts()`: List user's connected accounts
  - `disconnect_account()`: Disconnect email account

- **`quarantine_views.py`**: Quarantine management views
  - `list_quarantined_emails()`: List quarantined emails
  - `release_quarantined_email()`: Release quarantined email
  - `delete_quarantined_email()`: Delete quarantined email

- **`webhook_views.py`**: Webhook handlers
  - `gmail_webhook()`: Handle Gmail push notifications
  - `outlook_webhook()`: Handle Outlook push notifications
  - `verify_gmail_signature()`: Verify Gmail webhook signature

- **`__init__.py`**: View exports

#### Main View Files (Backward Compatibility)
- **`views.py`**: Re-exports from modular views
- **`auth_views.py`**: Re-exports from modular auth views + OAuth callbacks
- **`dashboard_views.py`**: Re-exports from modular dashboard views
- **`admin_views.py`**: Admin-specific views
- **`extension_views.py`**: Extension-specific API endpoints

#### Utilities
- **`db_utils.py`**: Database utility functions
  - `upsert_connected_account()`: Create or update connected account
  - `get_account_by_email()`: Get account by email address
  - `syslog()`: System logging utility
  - `decrypt_token()`: Decrypt OAuth tokens

- **`auth_utils.py`**: Authentication utilities
  - `require_auth()`: Decorator for authentication requirement

- **`email_validator.py`**: Email validation utilities
- **`url_reputation.py`**: URL reputation checking utilities
- **`oauth_utils.py`**: OAuth utility functions
- **`adapters.py`**: Email provider adapters

#### Management Commands (`management/commands/`)
- **`diagnose_quarantine.py`**: Diagnose quarantine issues
- **`fix_phishing_classifications.py`**: Fix phishing classifications
- **`fix_quarantine_missing.py`**: Fix missing quarantine entries
- **`fix_socialapps.py`**: Fix social app configurations
- **`recalculate_confidence_scores.py`**: Recalculate confidence scores
- **`reset_opened_emails.py`**: Reset opened email tracking
- **`set_admin.py`**: Set user as admin
- **`verify_opened_stats.py`**: Verify opened email statistics

#### Migrations (`migrations/`)
- Django database migration files

#### Other Files
- **`admin.py`**: Django admin configuration
- **`apps.py`**: Django app configuration
- **`signals.py`**: Django signal handlers
- **`tests.py`**: Test files

---

## 📁 Extension Structure (`extension/`)

### Source Files (`src/`) - ES6 Module Structure (for future build system)
**Note**: These files use ES6 modules and require a build step. Current implementation uses non-module JavaScript in `content/` directory.

#### Utilities (`utils/`)
- **`messaging.js`**: Message bus for extension communication (ES6 module version)
- **`dom.js`**: DOM extraction utilities (ES6 module version)
- **`indicators.js`**: Threat indicator UI utilities (ES6 module version)

#### Gmail Integration (`gmail/`)
- **`email-monitor.js`**: Gmail email monitoring (ES6 module version)

### Content Scripts (`content/`)
- **`gmail.js`**: Gmail content script (refactored, no ES6 modules)
  - Contains: MessageBus, DOMExtractor, ThreatIndicator utilities
  - Contains: GmailEmailMonitor class for email monitoring
  - Monitors Gmail interface and displays spam indicators
  - Handles email analysis requests and displays results

- **`gmail-refactored.js`**: Alternative refactored version (can replace gmail.js)
- **`outlook.js`**: Outlook content script (similar structure to Gmail)
- **`website-bridge.js`**: Website bridge for communication with web app
- **`styles.css`**: Content script styles for spam indicators

### Background (`background/`)
- **`service-worker.js`**: Service worker for background tasks
  - Message handling: Routes messages from content scripts and popup
  - API communication: Handles all backend API calls
  - Authentication management: Token storage and validation
  - Email analysis coordination: Processes email analysis requests
  - OAuth flow handling: Manages Gmail/Outlook account connections
  - Stats and account management: Fetches dashboard data

### Popup (`popup/`)
- **`popup.html`**: Popup HTML structure
  - Loading view
  - Not authenticated view
  - Authenticated view with stats, accounts, and quick actions

- **`popup.js`**: Popup script logic
  - Initialization and element management
  - Authentication status checking
  - Stats and accounts loading
  - Event handlers for all buttons
  - UI state management (loading/auth/not-auth views)

- **`popup.css`**: Popup styles
  - Responsive design
  - Stats grid layout
  - Button styles
  - Loading animations

### Options (`options/`)
- **`options.html`**: Options page HTML
- **`options.js`**: Options page script
- **`options.css`**: Options page styles

### Configuration
- **`manifest.json`**: Extension manifest (permissions, scripts, etc.)

### Assets
- **`assets/icons/`**: Extension icons (16x16, 32x32, 48x48, 128x128)

---

## 🔄 Data Flow

### Email Processing Flow
1. **Email Received** → Webhook triggers (`webhook_views.py`)
2. **Email Stored** → `Email` model created
3. **Authentication Check** → `EmailAuthResult` created (SPF/DKIM/DMARC)
4. **URL Analysis** → `URLAnalysis` created for each URL
5. **Classification** → `decision_engine.py` → `classification/classifier.py`
6. **Quarantine** → `QuarantinedEmail` created if needed
7. **Action Executed** → Email moved/deleted based on classification

### Authentication Flow
1. **User Login** → `auth_views.py` → `auth_service.py`
2. **Token Generated** → `Token` model created
3. **Session Created** → Django session
4. **API Requests** → Token in header → `auth_utils.require_auth`

### OAuth Flow (Email Account Connection)
1. **User Initiates** → `oauth_views.py` → `oauth_service.py`
2. **Redirect to Provider** → Google/Microsoft OAuth
3. **Callback Received** → `oauth_views.py` callback handler
4. **Tokens Exchanged** → `oauth_service.py`
5. **Account Saved** → `ConnectedAccount` model created
6. **Watch Setup** → Gmail watch or Outlook subscription

---

## 🗄️ Database Schema

### Key Models
- **User**: Django user model (extends with email, username)
- **ConnectedAccount**: OAuth-connected email accounts
- **Email**: Processed email messages
- **EmailAuthResult**: Authentication results (SPF/DKIM/DMARC)
- **URLAnalysis**: URL reputation analysis
- **ClassificationResult**: Final classification verdict
- **QuarantinedEmail**: Quarantined emails
- **SystemLog**: System event logs

### Relationships
- User → ConnectedAccount (1:N)
- User → Email (1:N)
- User → QuarantinedEmail (1:N)
- ConnectedAccount → Email (1:N)
- Email → EmailAuthResult (1:1)
- Email → URLAnalysis (1:N)
- Email → ClassificationResult (1:1)
- Email → QuarantinedEmail (1:N)

---

## 🔐 Security Features

1. **Token Authentication**: REST API uses token-based auth
2. **OAuth Encryption**: Tokens stored encrypted in database
3. **CSRF Protection**: Django CSRF protection enabled
4. **Webhook Verification**: Gmail webhook signature verification
5. **Input Validation**: All inputs validated and sanitized
6. **SQL Injection Protection**: Django ORM prevents SQL injection
7. **XSS Protection**: React escapes content by default

---

## 📊 Key Features

1. **Email Authentication**: SPF, DKIM, DMARC checking
2. **URL Reputation**: Google SafeBrowsing, URLhaus, URLScan.io
3. **Rule-Based Classification**: Configurable threat thresholds
4. **Quarantine Management**: Review and release/delete quarantined emails
5. **Dashboard Analytics**: User and admin dashboards with statistics
6. **Browser Extension**: Real-time email analysis in Gmail/Outlook
7. **OAuth Integration**: Secure email account connection
8. **Webhook Support**: Real-time email notifications

---

## 🚀 Deployment Considerations

### Frontend
- Build: `npm run build` → `dist/` directory
- Serve: Static files served via web server (Nginx, etc.)
- Environment: Vite handles environment variables

### Backend
- WSGI: Use Gunicorn or uWSGI
- ASGI: Use Uvicorn for async support
- Celery: Run separate worker processes
- Database: PostgreSQL recommended for production
- Static Files: Collect with `python manage.py collectstatic`

### Extension
- Build: Package extension files
- Distribution: Chrome Web Store / Firefox Add-ons
- Updates: Handle version updates in manifest

---

## 📝 Notes

- All files are kept under 200 lines for maintainability
- Services handle business logic, views handle HTTP
- Components are highly reusable and loosely coupled
- TypeScript provides type safety in frontend
- Django ORM provides database abstraction
- Modular structure allows easy testing and maintenance

