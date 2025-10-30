# vitanips/settings.py
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from decouple import config, Csv
from urllib.parse import urlparse
import dj_database_url
import logging
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# GDAL/GEOS Configuration for GeoDjango
# These paths are for macOS with Homebrew installations
GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.11.4_1/lib/libgdal.37.dylib'
GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/geos/3.14.0/lib/libgeos_c.dylib'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

CSRF_TRUSTED_ORIGINS = ['https://vitanips.onrender.com']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_gis',
    'django_filters',
    'corsheaders',
    'storages',
    'twilio',
    'push_notifications',
    'rest_framework_simplejwt',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'dj_rest_auth',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
    
    # Local apps
    'users',
    'doctors',
    'pharmacy',
    'health',
    'insurance',
    'emergency',
    'notifications'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'vitanips.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vitanips.wsgi.application'

# Database
DJANGO_ENV = config('DJANGO_ENV', default='development')
if DJANGO_ENV == 'development':
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': config('DEV_DB_NAME', default='vitanips_dev'),
            'USER': config('DEV_DB_USER', default=os.environ.get('USER', 'postgres')),
            'PASSWORD': config('DEV_DB_PASSWORD', default=''),
            'HOST': config('DEV_DB_HOST', default='localhost'),
            'PORT': config('DEV_DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.parse(
            config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
            engine='django.contrib.gis.db.backends.postgis',  # Ensure PostGIS engine
        )
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
]
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
logger = logging.getLogger(__name__)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# if DJANGO_ENV == 'development':
#     STATIC_URL = '/static/'
#     STATIC_ROOT = BASE_DIR / 'staticfiles'
#     STATICFILES_DIRS = [BASE_DIR / 'static']
#     MEDIA_URL = '/media/'
#     MEDIA_ROOT = BASE_DIR / 'media'
# else:
#     STATIC_URL = '/static/'
#     STATIC_ROOT = BASE_DIR / 'staticfiles'
#     STATICFILES_DIRS = [BASE_DIR / 'static']
#     STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

#     DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#     AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
#     AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
#     AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
#     AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', default='us-east-2')
#     AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
#     AWS_DEFAULT_IMAGE_PATH = "media/defaults/default_product_image.jpg"

#     AWS_QUERYSTRING_AUTH = False
#     AWS_S3_FILE_OVERWRITE = False
#     AWS_DEFAULT_ACL = 'public-read'
#     AWS_S3_SIGNATURE_VERSION = 's3v4'
#     AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
#     MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'VitaNips Healthcare API',
    'DESCRIPTION': 'Comprehensive healthcare management platform API - Appointments, Prescriptions, Telehealth, and more',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'VitaNips Support',
        'email': 'support@vitanips.com',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'TAGS': [
        {'name': 'Authentication', 'description': 'User registration, login, and JWT management'},
        {'name': 'Users', 'description': 'User profile and account management'},
        {'name': 'Doctors', 'description': 'Doctor profiles, availability, and reviews'},
        {'name': 'Appointments', 'description': 'Book, manage, and track appointments'},
        {'name': 'Prescriptions', 'description': 'View and manage prescriptions'},
        {'name': 'Pharmacy', 'description': 'Pharmacies, medications, and orders'},
        {'name': 'Health', 'description': 'Vital signs, symptoms, medical documents'},
        {'name': 'Insurance', 'description': 'Insurance coverage and claims'},
        {'name': 'Emergency', 'description': 'Emergency services and SOS alerts'},
        {'name': 'Notifications', 'description': 'In-app notifications and preferences'},
    ],
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
}

# dj-rest-auth settings
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False,
    'TOKEN_MODEL': None,
}

# CORS settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# Site ID for django-allauth
SITE_ID = 1

# --- Celery Configuration ---
CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_CACHE_BACKEND = 'default'

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-appointment-reminders': {
        'task': 'notifications.tasks.check_appointment_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'check-medication-refill-reminders': {
        'task': 'notifications.tasks.check_medication_refill_reminders',
        'schedule': crontab(hour='9', minute='0'),  # Daily at 9 AM
    },
    'process-scheduled-notifications': {
        'task': 'notifications.tasks.process_scheduled_notifications',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'retry-failed-deliveries': {
        'task': 'notifications.tasks.retry_failed_deliveries',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour='2', minute='0'),  # Daily at 2 AM
    },
}

# --- Email Configuration ---
# Intelligently select email backend based on environment and available credentials
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='VitaNips <noreply@vitanips.com>')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# SMTP Configuration (Gmail, etc.)
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Django Anymail (SendGrid, AWS SES, Mailgun, etc.)
# Install with: pip install django-anymail[sendgrid] or django-anymail[amazon-ses]
if EMAIL_BACKEND in ['anymail.backends.sendgrid.EmailBackend', 
                      'anymail.backends.amazon_ses.EmailBackend',
                      'anymail.backends.mailgun.EmailBackend']:
    ANYMAIL = {}
    
    # SendGrid Configuration
    if 'sendgrid' in EMAIL_BACKEND:
        ANYMAIL = {
            "SENDGRID_API_KEY": config('SENDGRID_API_KEY', default=''),
            "SENDGRID_GENERATE_MESSAGE_ID": True,
            "SENDGRID_MERGE_FIELD_FORMAT": "-{}-",
        }
    
    # AWS SES Configuration
    elif 'amazon_ses' in EMAIL_BACKEND:
        ANYMAIL = {
            "AMAZON_SES_REGION": config('AWS_SES_REGION_NAME', default='us-east-1'),
        }
        # AWS credentials should be set in AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
    
    # Mailgun Configuration
    elif 'mailgun' in EMAIL_BACKEND:
        ANYMAIL = {
            "MAILGUN_API_KEY": config('MAILGUN_API_KEY', default=''),
            "MAILGUN_SENDER_DOMAIN": config('MAILGUN_SENDER_DOMAIN', default=''),
        }

# --- Twilio Configuration ---
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
TWILIO_API_KEY_SID = config('TWILIO_API_KEY_SID', default='')
TWILIO_API_KEY_SECRET = config('TWILIO_API_KEY_SECRET', default='')

# --- Push Notifications Configuration ---
# FCM HTTP v1 API (Modern, Recommended)
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = BASE_DIR / config('FIREBASE_SERVICE_ACCOUNT_KEY', default='firebase-service-account.json')

PUSH_NOTIFICATIONS_SETTINGS = {
    # Firebase Cloud Messaging (FCM) - HTTP v1 API
    # Download service account JSON from Firebase Console
    "FCM_SERVICE_ACCOUNT_KEY": str(FIREBASE_SERVICE_ACCOUNT_KEY_PATH) if FIREBASE_SERVICE_ACCOUNT_KEY_PATH.exists() else None,
    
    # Legacy API (deprecated but kept for backward compatibility)
    # Only used if service account key is not available
    "FCM_API_KEY": config('FCM_SERVER_KEY', default=None),
    
    # Apple Push Notification Service (APNS) - For iOS apps
    "APNS_CERTIFICATE": config('APNS_CERTIFICATE_PATH', default=None),
    "APNS_PRIVATE_KEY_PATH": config('APNS_PRIVATE_KEY_PATH', default=None),
    "APNS_KEY_ID": config('APNS_KEY_ID', default=None),
    "APNS_TEAM_ID": config('APNS_TEAM_ID', default=None),
    "APNS_TOPIC": config('APNS_BUNDLE_ID', default=None),
    "APNS_USE_SANDBOX": config('APNS_USE_SANDBOX', default=True, cast=bool),
    "APNS_USE_ALTERNATIVE_PORT": False,
    
    # API Settings
    "FCM_MAX_RECIPIENTS": 1000,
    "APNS_MAX_RECIPIENTS": 100,
}

# Log push notification configuration status
if FIREBASE_SERVICE_ACCOUNT_KEY_PATH.exists():
    logger.info(f"✓ FCM configured with service account: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH.name}")
elif PUSH_NOTIFICATIONS_SETTINGS.get("FCM_API_KEY"):
    logger.warning("⚠ FCM using legacy API key (deprecated). Consider migrating to service account.")
else:
    logger.warning("⚠ FCM not configured. Push notifications will be disabled.")

# Logging
# Ensure log directory exists
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'app.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': True,
        },
        'storages': {
            'handlers': ['file', 'console'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': True,
        },
    },
}