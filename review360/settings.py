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
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

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
    "iam",
    "academics",
    "learning",
    "followup",
    "compliance",
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware"
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
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
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
# Prefer explicit origins; keep a dev-only escape hatch
_cors_allow_all = os.environ.get("CORS_ALLOW_ALL", "0") == "1"
if _cors_allow_all and not DEBUG:
    _cors_allow_all = False
    # In prod we never allow all; rely on explicit origins
CORS_ALLOW_ALL_ORIGINS = _cors_allow_all
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",") if o
]


# DRF + JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
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
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_MIN", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # For Transport Layer Security
EMAIL_HOST_USER = 'gmi.tn.dev.akmarimuthu@gmail.com'  # Your full Gmail address
EMAIL_HOST_PASSWORD = 'ragmvkoqvlvvzalr'

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
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "security": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "iam.User"


