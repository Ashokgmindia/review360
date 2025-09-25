from pathlib import Path
import os
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

# Security
# Fail fast if missing in non-debug environments
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "dev-only-insecure-key" if os.environ.get("DJANGO_DEBUG", "1") == "1" else None
)
if SECRET_KEY is None:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    h
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h
]

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "iam",
    "academics",
    "learning",
    "followup",
    "compliance",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "iam.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "review360.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "review360.wsgi.application"
ASGI_APPLICATION = "review360.asgi.application"


# Database (Postgres via env)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "review360"),
        "USER": os.environ.get("POSTGRES_USER", "review360"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "review360"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []

# WhiteNoise: compressed + hashed static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# CORS
# When credentials are included, we cannot use wildcard origins
# So we need to explicitly list allowed origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Never use wildcard when credentials are enabled

# Default allowed origins for development
_default_origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]

# Add production origins if specified
_production_origins = [
    o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]

CORS_ALLOWED_ORIGINS = _default_origins + _production_origins

# Regex patterns for dynamic origins (useful for development)
CORS_ALLOWED_ORIGINS_REGEXES = [
    r"^http://localhost:\d+$",  # Allow any localhost port
    r"^http://127\.0\.0\.1:\d+$",  # Allow any 127.0.0.1 port
    r"^https://.*\.duckdns\.org:\d+$",  # Allow https duckdns subdomains with ports
    r"^http://.*\.duckdns\.org:\d+$",  # Allow http duckdns subdomains with ports
]

# Additional CORS headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# DRF + JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Pagination
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": int(os.environ.get("DRF_PAGE_SIZE", "50")),
    # Throttling (tunable via env)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": os.environ.get("DRF_THROTTLE_USER", "1000/hour"),
        "anon": os.environ.get("DRF_THROTTLE_ANON", "100/hour"),
        "login": os.environ.get("DRF_THROTTLE_LOGIN", "20/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_MIN", "30"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.environ.get("JWT_REFRESH_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # For Transport Layer Security
EMAIL_HOST_USER = "gmi.tn.dev.akmarimuthu@gmail.com"  # Your full Gmail address
EMAIL_HOST_PASSWORD = "ragmvkoqvlvvzalr"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Google Calendar Integration Settings
GOOGLE_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'google_client_secrets.json')
GOOGLE_CREDENTIALS_FILE = os.path.join(BASE_DIR, 'google_credentials.json')

# Celery Configuration for Background Tasks
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Review360 API",
    "DESCRIPTION": "API documentation for Review360",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {"url": "/", "description": "Current server"},
    ],
    # Global security requirement
    "SECURITY": [{"BearerAuth": []}],
    # Define JWT bearer scheme explicitly so UIs show the Authorize button correctly
    "SECURITY_SCHEMES": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    },
    # Order the API endpoints by tags to match the specified order
    "TAGS": [
        {"name": "IAM", "description": "Identity and Access Management"},
        {"name": "Academics", "description": "Academic management including classes, students, teachers, and subjects"},
        {"name": "Learning", "description": "Learning activities and validations"},
        {"name": "Followup", "description": "Follow-up sessions and tracking"},
        {"name": "Compliance", "description": "Audit logs and compliance records"},
    ],
    # Sort operations by tags to maintain the specified order
    "SORT_OPERATIONS": True,
    "SORT_TAGS": True,
}

# Logging (JSON-ready minimal config)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "security": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "iam.User"
