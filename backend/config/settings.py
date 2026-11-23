
"""
Django settings for DealerOS.

Local development:
    React: http://localhost:5173
    Django: http://127.0.0.1:8000

Production:
    Frontend: Vercel
    Backend: Render
    Database: PostgreSQL
"""

import os
from pathlib import Path

import dj_database_url


# ==================================================
# BASE DIRECTORY
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# SECURITY
# ==================================================

# Local fallback is only for development.
# Production requires SECRET_KEY in environment variables.
LOCAL_SECRET_KEY = "dealeros-local-development-only-change-me"

SECRET_KEY = os.environ.get("SECRET_KEY", LOCAL_SECRET_KEY)

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

if not DEBUG and (
    not os.environ.get("SECRET_KEY")
    or SECRET_KEY == LOCAL_SECRET_KEY
):
    raise RuntimeError(
        "Set a secure SECRET_KEY environment variable in production."
    )

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
]

extra_hosts = os.environ.get("ALLOWED_HOSTS", "")

if extra_hosts:
    ALLOWED_HOSTS.extend(
        host.strip()
        for host in extra_hosts.split(",")
        if host.strip()
    )


# ==================================================
# INSTALLED APPLICATIONS
# ==================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party packages
    "rest_framework",
    "corsheaders",

    # DealerOS application
    "reconcile",
]


# ==================================================
# MIDDLEWARE
# ==================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Static files for Render
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # React frontend CORS
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==================================================
# URL CONFIGURATION
# ==================================================

ROOT_URLCONF = "config.urls"


# ==================================================
# TEMPLATES
# ==================================================

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


# ==================================================
# WSGI
# ==================================================

WSGI_APPLICATION = "config.wsgi.application"


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

# Local development uses SQLite.
# Render production uses PostgreSQL through DATABASE_URL.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

database_url = os.environ.get("DATABASE_URL")

if database_url:
    DATABASES["default"] = dj_database_url.parse(
        database_url,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )


# ==================================================
# PASSWORD VALIDATION
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==================================================
# INTERNATIONALIZATION
# ==================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ==================================================
# STATIC FILES
# ==================================================

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


# ==================================================
# DEFAULT PRIMARY KEY
# ==================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================================================
# DJANGO REST FRAMEWORK
# ==================================================

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}


# ==================================================
# CORS CONFIGURATION
# ==================================================

# Local React development URLs
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Set FRONTEND_URL on Render after deploying Vercel.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "").rstrip("/")

if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

# Do not allow every origin.
CORS_ALLOW_ALL_ORIGINS = False


# ==================================================
# CSRF CONFIGURATION
# ==================================================

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if FRONTEND_URL:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)


# ==================================================
# PRODUCTION SECURITY
# ==================================================

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_HSTS_SECONDS = 3600

    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

    SECURE_HSTS_PRELOAD = False
