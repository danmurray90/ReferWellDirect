"""
Base settings for ReferWell Direct project.
"""
import os
from pathlib import Path

import environ

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    DB_NAME=(str, "referwell"),
    DB_USER=(str, "referwell"),
    DB_PASSWORD=(str, "referwell"),
    DB_HOST=(str, "localhost"),
    DB_PORT=(int, 5432),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=(str, "redis://localhost:6379/0"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    EMAIL_HOST=(str, "localhost"),
    EMAIL_PORT=(int, 1025),
    EMAIL_USE_TLS=(bool, False),
    FEATURE_GOV_UK_NOTIFY=(bool, False),
    FEATURE_STRIPE_CONNECT=(bool, False),
    FEATURE_NHS_LOGIN=(bool, False),
    FEATURE_PDS_ODS=(bool, False),
    FEATURE_ERS=(bool, False),
    MATCHING_EMBEDDING_MODEL=(str, "sentence-transformers/all-MiniLM-L6-v2"),
    MATCHING_EMBEDDING_DIMENSION=(int, 384),
    MATCHING_CALIBRATION_METHOD=(str, "isotonic"),
    MATCHING_THRESHOLD_AUTO=(float, 0.7),
    MATCHING_THRESHOLD_HIGH_TOUCH=(float, 0.5),
    LOG_LEVEL=(str, "INFO"),
    LOG_FORMAT=(str, "json"),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
)

# Read .env file
environ.Env.read_env(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # PostGIS support
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_extensions",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
    "drf_spectacular_sidecar",
]

LOCAL_APPS = [
    "accounts",
    "referrals",
    "catalogue",
    "matching",
    "inbox",
    "payments",
    "ops",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "referwell.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "referwell.wsgi.application"
ASGI_APPLICATION = "referwell.asgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication settings
LOGIN_URL = "/accounts/signin/"
LOGIN_REDIRECT_URL = "/referrals/"
LOGOUT_REDIRECT_URL = "/accounts/signin/"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "ReferWell Direct API",
    "DESCRIPTION": "API for ReferWell Direct - Mental Health Referral Management System",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "SCHEMA_PATH_PREFIX": "/api/",
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.referwell.direct", "description": "Production server"},
    ],
    "TAGS": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization",
        },
        {"name": "Referrals", "description": "Referral management and tracking"},
        {
            "name": "Appointments",
            "description": "Appointment scheduling and management",
        },
        {"name": "Candidates", "description": "Psychologist candidate matching"},
        {"name": "Analytics", "description": "Analytics and reporting"},
        {
            "name": "Bulk Operations",
            "description": "Bulk operations for referrals and appointments",
        },
        {"name": "Search", "description": "Advanced search and filtering"},
    ],
    "EXTENSIONS_INFO": {
        "x-logo": {"url": "/static/images/logo.png", "altText": "ReferWell Direct Logo"}
    },
    "CONTACT": {
        "name": "ReferWell Direct Support",
        "email": "support@referwell.direct",
        "url": "https://referwell.direct/support",
    },
    "LICENSE": {"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    "EXTERNAL_DOCS": {
        "description": "Find more information about ReferWell Direct",
        "url": "https://referwell.direct/docs",
    },
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "supportedSubmitMethods": ["get", "post", "put", "patch", "delete"],
        "validatorUrl": None,
        "oauth2RedirectUrl": "/api/schema/swagger-ui/oauth2-redirect.html",
        "preauthorizeBasic": False,
        "preauthorizeApiKey": False,
    },
    "REDOC_UI_SETTINGS": {
        "hideDownloadButton": False,
        "hideHostname": False,
        "hideLoading": False,
        "nativeScrollbars": False,
        "disableSearch": False,
        "onlyRequiredInSamples": False,
        "sortPropsAlphabetically": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Celery Configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Email Configuration
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

# Feature Flags
FEATURE_GOV_UK_NOTIFY = env("FEATURE_GOV_UK_NOTIFY")
FEATURE_STRIPE_CONNECT = env("FEATURE_STRIPE_CONNECT")
FEATURE_NHS_LOGIN = env("FEATURE_NHS_LOGIN")
FEATURE_PDS_ODS = env("FEATURE_PDS_ODS")
FEATURE_ERS = env("FEATURE_ERS")

# Matching Engine Configuration
MATCHING_EMBEDDING_MODEL = env("MATCHING_EMBEDDING_MODEL")
MATCHING_EMBEDDING_DIMENSION = env("MATCHING_EMBEDDING_DIMENSION")
MATCHING_CALIBRATION_METHOD = env("MATCHING_CALIBRATION_METHOD")
MATCHING_THRESHOLD_AUTO = env("MATCHING_THRESHOLD_AUTO")
MATCHING_THRESHOLD_HIGH_TOUCH = env("MATCHING_THRESHOLD_HIGH_TOUCH")

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if env("LOG_FORMAT") == "json" else "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL"),
            "propagate": False,
        },
        "referwell": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL"),
            "propagate": False,
        },
    },
}

# Security Settings
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# GDAL Configuration
GDAL_LIBRARY_PATH = "/opt/homebrew/Cellar/gdal/3.11.4/lib/libgdal.37.3.11.4.dylib"
GEOS_LIBRARY_PATH = "/opt/homebrew/Cellar/geos/3.14.0/lib/libgeos_c.1.20.4.dylib"

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Session Cache
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
