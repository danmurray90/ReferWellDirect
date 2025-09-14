"""
Production settings for ReferWell Direct project.
"""
from .base import *

# Override base settings for production
DEBUG = False

# Production security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production CORS settings (restrictive)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# Production email backend (configure with real SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Production logging
LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': '/var/log/referwell/django.log',
    'maxBytes': 1024 * 1024 * 15,  # 15MB
    'backupCount': 10,
    'formatter': 'json',
}

LOGGING['loggers']['django']['handlers'] = ['file']
LOGGING['loggers']['referwell']['handlers'] = ['file']

# Production static files
STATIC_ROOT = '/var/www/referwell/static/'
MEDIA_ROOT = '/var/www/referwell/media/'

# Production database settings
DATABASES['default'].update({
    'OPTIONS': {
        'sslmode': 'require',
    }
})

# Production cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Production session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Production feature flags (can be overridden by environment)
FEATURE_GOV_UK_NOTIFY = env('FEATURE_GOV_UK_NOTIFY', default=False)
FEATURE_STRIPE_CONNECT = env('FEATURE_STRIPE_CONNECT', default=False)
FEATURE_NHS_LOGIN = env('FEATURE_NHS_LOGIN', default=False)
FEATURE_PDS_ODS = env('FEATURE_PDS_ODS', default=False)
FEATURE_ERS = env('FEATURE_ERS', default=False)

# Production matching thresholds
MATCHING_THRESHOLD_AUTO = env('MATCHING_THRESHOLD_AUTO', default=0.7)
MATCHING_THRESHOLD_HIGH_TOUCH = env('MATCHING_THRESHOLD_HIGH_TOUCH', default=0.5)

# Production logging level
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['referwell']['level'] = 'INFO'

# Production allowed hosts (must be set in environment)
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Production secret key (must be set in environment)
SECRET_KEY = env('SECRET_KEY')

# Production database configuration
DATABASES['default'].update({
    'NAME': env('DB_NAME'),
    'USER': env('DB_USER'),
    'PASSWORD': env('DB_PASSWORD'),
    'HOST': env('DB_HOST'),
    'PORT': env('DB_PORT'),
})

# Production Redis configuration
REDIS_URL = env('REDIS_URL')
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

# Production monitoring (if enabled)
if env('ENABLE_MONITORING', default=False):
    INSTALLED_APPS += ['django_prometheus']
    MIDDLEWARE = ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + MIDDLEWARE + ['django_prometheus.middleware.PrometheusAfterMiddleware']

# Production error reporting (if configured)
if env('SENTRY_DSN', default=''):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )
