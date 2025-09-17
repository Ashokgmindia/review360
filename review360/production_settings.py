"""
Production settings for Review360 multi-tenant SaaS application.

This module contains production-specific configurations that override
the base settings for security, performance, and reliability.
"""

import os
from pathlib import Path
from .settings import *

# Security
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",
            "connect_timeout": 10,
        },
        "CONN_MAX_AGE": 60,
    }
}

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "review360",
        "TIMEOUT": 300,
    }
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@review360.com")

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/review360/django.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "json",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/review360/security.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "review360": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# DRF Configuration
REST_FRAMEWORK.update({
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": int(os.environ.get("DRF_PAGE_SIZE", "50")),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("DRF_THROTTLE_ANON", "100/hour"),
        "user": os.environ.get("DRF_THROTTLE_USER", "1000/hour"),
        "login": os.environ.get("DRF_THROTTLE_LOGIN", "20/hour"),
    },
})

# JWT Configuration
SIMPLE_JWT.update({
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_MIN", "30"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.environ.get("JWT_REFRESH_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
})

# Static Files
STATIC_ROOT = "/var/www/review360/static/"
MEDIA_ROOT = "/var/www/review360/media/"

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Performance Settings
CONN_MAX_AGE = 60
USE_TZ = True
TIME_ZONE = "UTC"

# Monitoring and Health Checks
HEALTH_CHECK = {
    "DISK_USAGE_MAX": 90,  # percent
    "MEMORY_MIN": 100,  # in MB
}

# Celery Configuration (if using async tasks)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Sentry Configuration (if using error tracking)
if os.environ.get("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )

# Admin Configuration
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/")

# API Documentation
SPECTACULAR_SETTINGS.update({
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
    "SERVE_AUTHENTICATION": ["rest_framework.authentication.SessionAuthentication"],
})

# Backup Configuration
BACKUP_DIR = "/var/backups/review360"
BACKUP_RETENTION_DAYS = 30

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# Security Middleware
MIDDLEWARE.insert(0, "django.middleware.security.SecurityMiddleware")
MIDDLEWARE.append("django.middleware.clickjacking.XFrameOptionsMiddleware")

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)

# Additional Security Headers
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Database Connection Pooling
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["OPTIONS"]["MAX_CONNS"] = 20

# File Storage (if using cloud storage)
if os.environ.get("USE_S3"):
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
    
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
