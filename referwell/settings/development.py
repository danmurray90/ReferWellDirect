"""
Development settings for ReferWell Direct project.
"""
from .base import *

# Override base settings for development
DEBUG = True

# Add debug toolbar for development
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

    # Debug toolbar configuration
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

# Development-specific CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development logging
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]
LOGGING["loggers"]["referwell"]["level"] = "DEBUG"  # type: ignore[index]

# Development-specific settings
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Disable SSL redirects in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development database (can be overridden by environment)
DATABASES["default"].update(
    {
        "OPTIONS": {
            "sslmode": "prefer",
        }
    }
)

# Development static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Development media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Development cache (use dummy cache for simplicity)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Development session backend
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Development-specific feature flags (can be overridden by environment)
FEATURE_GOV_UK_NOTIFY = False
FEATURE_STRIPE_CONNECT = False
FEATURE_NHS_LOGIN = False
FEATURE_PDS_ODS = False
FEATURE_ERS = False

# Development matching thresholds (more permissive for testing)
MATCHING_THRESHOLD_AUTO = 0.5
MATCHING_THRESHOLD_HIGH_TOUCH = 0.3

# Development logging configuration
LOGGING["handlers"]["file"] = {  # type: ignore[index]
    "class": "logging.FileHandler",
    "filename": BASE_DIR / "logs" / "development.log",
    "formatter": "verbose",
}

LOGGING["loggers"]["referwell"]["handlers"] = ["console", "file"]  # type: ignore[index]

# Create logs directory if it doesn't exist
import os

os.makedirs(BASE_DIR / "logs", exist_ok=True)
