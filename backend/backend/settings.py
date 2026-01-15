# backend/backend/settings.py

from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import os
from celery.schedules import crontab

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-5$^5v05%v-b^hc**z@j946cz9p$820we1915m1!fsvvt2dolnu')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS
# We add 'backend' to allow Docker containers to talk to each other
ALLOWED_HOSTS = ['myvelorum.com', 'd37ct6eknowd73.cloudfront.net', '3.143.240.176', "localhost", '127.0.0.1', 'backend']

# Application definition
INSTALLED_APPS = [
    'daphne', # Must be at the top for ASGI/WebSockets support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'storages',
    'channels', # Required for WebSockets
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# --- ARCHITECTURE CHANGE: ASGI for WebSockets ---
# Resume Claim: "Utilizing WebSocket connections"
# We switch from WSGI (Sync) to ASGI (Async) as the primary entry point
WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'

# --- ARCHITECTURE CHANGE: PostgreSQL (Resume Claim) ---
# If DB_HOST is set (e.g., by Docker), use PostgreSQL.
# Otherwise, fall back to SQLite (so you can verify things locally if needed).
if os.getenv('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'velorum_db'),
            'USER': os.getenv('DB_USER', 'velorum_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password123'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- ARCHITECTURE CHANGE: Redis & Channels ---
# Resume Claim: "Engineered Redis caching" & "WebSockets"

# 1. Redis Cache Config
# Note: SSL is disabled for local Docker/Dev. Enable it only if using AWS ElastiCache.
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # 'SSL': True,  <-- DISABLED for local Docker development
        }
    }
}

# 2. Channels Layer (WebSockets glue)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# --- CELERY CONFIG ---
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1')
CELERY_TIMEZONE = 'US/Eastern'
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'cache_all_stocks_during_trading_hours': {
        'task': 'api.tasks.cache_all_stocks',
        'schedule': crontab(minute='*/1', hour='9-15', day_of_week='1-5'),
    },
    'cache_stocks_at_market_close': {
        'task': 'api.tasks.cache_all_stocks',
        'schedule': crontab(minute=0, hour=16, day_of_week='1-5'),
    },
    'cache_financial_and_profile_data_daily': {
        'task': 'api.tasks.cache_financial_and_profile_data',
        'schedule': crontab(hour=0, minute=0),
    },
    'capture-daily-portfolio-value': {
        'task': 'api.tasks.capture_daily_portfolio_value',
        'schedule': crontab(minute=0, hour=17, day_of_week='1-5'),
    },
}

# --- JWT AUTHENTICATION ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES & AWS S3 ---
# If AWS keys are present, use S3. Otherwise use local static files.
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

if AWS_ACCESS_KEY_ID:
    AWS_S3_REGION_NAME = 'us-east-2'  
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/'
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
else:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://myvelorum.com',
    "http://localhost:5173",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://myvelorum.com',
    "http://localhost:5173",
    "http://localhost:3000",
]