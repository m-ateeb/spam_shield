from pathlib import Path
import os
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated

# Optional: dj_database_url for parsing DATABASE_URL
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

load_dotenv()  # Load variables from .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-pa9+q-xp5emsj7ytnd#@&db&k5l!v$-ysv-g8!uyi(gp5l&ra+')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.yourdomain.com', 'unrung-undegenerating-les.ngrok-free.dev', 'localhost:5173']

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/oauth/google/callback"

MICROSOFT_REDIRECT_URI = f"{FRONTEND_URL}/oauth/microsoft/callback"



# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    
    # Local apps
    'email_connector',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# DEV ONLY: allow all origins
CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:5173",
#     "https://yourfrontend.com",
# ]

# CSRF Trusted Origins (for logout and other POST requests from frontend)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]


ROOT_URLCONF = 'spam_shield.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'spam_shield.wsgi.application'

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and dj_database_url:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
else:
    # Fallback to individual database settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'inbox_guardian'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# Supabase (Optional - Database only - not for auth)
# Only set these if you're using Supabase for data storage
SUPABASE_URL = os.getenv('SUPABASE_URL', None)
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', None)  # Server-only for database operations

# OAuth Credentials
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'http://localhost:8000')  # Fallback for dev

# Redirect URIs
GOOGLE_REDIRECT_URI = f"{WEBHOOK_URL.rstrip('/')}/oauth/google/callback/"
MICROSOFT_REDIRECT_URI = f"{WEBHOOK_URL.rstrip('/')}/oauth/microsoft/callback/"

# Fernet Key for Token Encryption
FERNET_KEY = os.getenv('FERNET_KEY')

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'spam_shield.authentication.DjangoTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Django Allauth Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
# Updated for django-allauth 0.60+
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
LOGIN_REDIRECT_URL = '/api/auth/callback/'
LOGOUT_REDIRECT_URL = '/'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = False  # We don't need to store OAuth tokens for user auth

# Custom Allauth Adapters
SOCIALACCOUNT_ADAPTER = 'email_connector.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'email_connector.adapters.CustomAccountAdapter'

# Social Account Providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': ''
        }
    },
    'microsoft': {
        'SCOPE': [
            'User.Read',
            'openid',
            'profile',
            'email',
        ],
        'APP': {
            'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
            'secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
            'key': ''
        }
    }
}

# Important: Set the correct callback URL for OAuth
# In Google OAuth Console, add: http://localhost:8000/accounts/google/login/callback/
# In Microsoft Azure Portal, add: http://localhost:8000/accounts/microsoft/login/callback/

# CELERY + UPTASH REDIS CLOUD
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_WORKER_POOL = 'solo'

# SSL FIX FOR rediss:// (Upstash)
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'ssl_cert_reqs': 'CERT_NONE'
}
CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': 'CERT_NONE'
}

# Email Processing Configuration
EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', 10))  # Configurable batch size
TOKEN_REFRESH_BUFFER_MINUTES = 5  # Refresh tokens 5 mins before expiry