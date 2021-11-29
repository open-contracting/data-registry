"""
Django settings for the project.

Generated by "django-admin startproject" using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from glob import glob
from pathlib import Path

import dj_database_url
import sentry_sdk
from django.utils.translation import gettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

production = os.getenv("DJANGO_ENV") == "production"
local_access = "LOCAL_ACCESS" in os.environ or "ALLOWED_HOSTS" not in os.environ

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "72icl@l(^0qr$9z-5od3ooo&7qw0d4199k3(&kl+%y!d&!!tq!")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not production

ALLOWED_HOSTS = [".localhost", "127.0.0.1", "[::1]", "0.0.0.0"]
if "ALLOWED_HOSTS" in os.environ:
    ALLOWED_HOSTS.extend(os.getenv("ALLOWED_HOSTS").split(","))


# Application definition

INSTALLED_APPS = [
    "modeltranslation",
    "core.apps.CoreAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "data_registry",
    "markdownx",
    "exporter",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.from_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(default="postgresql:///data_registry?application_name=data_registry"),
    "kingfisher_process": dj_database_url.config(
        env="KINGFISHER_PROCESS_DATABASE_URL",
        default="postgresql:///kingfisher_process?application_name=data_registry",
    ),
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

if production:
    STATIC_VERSION = os.getenv("STATIC_VERSION")
    STATIC_URL = "/static/{}/".format(STATIC_VERSION)
else:
    STATIC_URL = "/static/"


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Project-specific Django configuration

LOCALE_PATHS = glob(str(BASE_DIR / "**" / "locale"))

STATIC_ROOT = BASE_DIR / "static"

# https://docs.djangoproject.com/en/3.2/topics/logging/#django-security
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/
if production and not local_access:
    # Run: env DJANGO_ENV=production SECURE_HSTS_SECONDS=1 ./manage.py check --deploy
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_REFERRER_POLICY = "same-origin"  # default in Django >= 3.1

    # https://docs.djangoproject.com/en/3.2/ref/middleware/#http-strict-transport-security
    if "SECURE_HSTS_SECONDS" in os.environ:
        SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS"))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True

# https://docs.djangoproject.com/en/3.2/ref/settings/#secure-proxy-ssl-header
if "DJANGO_PROXY" in os.environ:
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/3.2/ref/settings/#email
if production:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = os.getenv("EMAIL_PORT")
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = "EMAIL_USE_TLS" in os.environ
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LANGUAGES = (
    ("en", _("English")),
    ("es", _("Spanish")),
    ("ru", _("Russian")),
)

DEFAULT_FROM_EMAIL = "noreply@noreply.open-contracting.org"

USE_THOUSAND_SEPARATOR = True


# Dependency configuration

if "SENTRY_DSN" in os.environ:
    # https://docs.sentry.io/platforms/python/logging/#ignoring-a-logger
    ignore_logger("django.security.DisallowedHost")
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0,  # The Sentry plan does not include Performance.
    )

# https://django-modeltranslation.readthedocs.io/en/latest/installation.html#modeltranslation-default-language
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"

# https://neutronx.github.io/django-markdownx/customization/#markdownx_markdownify_function
MARKDOWNX_MARKDOWNIFY_FUNCTION = "data_registry.utils.markdownify"


# Project configuration

FATHOM = {
    "domain": os.getenv("FATHOM_ANALYTICS_DOMAIN") or "cdn.usefathom.com",
    "id": os.getenv("FATHOM_ANALYTICS_ID"),
}

# The email to which form feedback is sent.
FEEDBACK_EMAIL = os.getenv("FEEDBACK_EMAIL", "jmckinney@open-contracting.org")

# The connection string for RabbitMQ.
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://localhost")
# The name of the RabbitMQ exchange. Follow the pattern `{project}_{service}_{environment}`.
RABBIT_EXCHANGE_NAME = os.getenv("RABBIT_EXCHANGE_NAME", "data_registry_development")

# The job tasks to run.
JOB_TASKS_PLAN = ["collect", "process", "pelican", "exporter"]

SCRAPYD = {
    # The base URL of Scrapyd.
    "url": os.getenv("SCRAPYD_URL"),
    # The project within Scrapyd.
    "project": os.getenv("SCRAPYD_PROJECT", "kingfisher"),
}
# The directory from which to delete the files written by Kingfisher Collect. If Kingfisher Collect and the Data
# Registry share a filesystem, this will be the same value for both services.
# WARNING: If you change the production default, update `Dockerfile_django` and `docker-compose.yaml` to match.
KINGFISHER_COLLECT_FILES_STORE = os.getenv(
    "KINGFISHER_COLLECT_FILES_STORE", "/data/collect" if production else BASE_DIR / "data" / "collect"
)

# The base URL of Kingfisher Process.
KINGFISHER_PROCESS_URL = os.getenv("KINGFISHER_PROCESS_URL")

# The base URL of Pelican frontend.
PELICAN_FRONTEND_URL = os.getenv("PELICAN_FRONTEND_URL")

# WARNING: If you change the production default, update `Dockerfile_django` and `docker-compose.yaml` to match.
EXPORTER_DIR = os.getenv("EXPORTER_DIR", "/data/storage/exporter_dumps" if production else BASE_DIR / "data" / "exporter")
# The batch size of compiled releases to extract from Kingfisher Process.
EXPORTER_PAGE_SIZE = 10000

# The base URL of Spoonbill.
SPOONBILL_URL = os.getenv("SPOONBILL_URL", "https://flatten.open-contracting.org")
SPOONBILL_API_USERNAME = os.getenv("SPOONBILL_API_USERNAME")
SPOONBILL_API_PASSWORD = os.getenv("SPOONBILL_API_PASSWORD")
