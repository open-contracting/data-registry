import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403,F401

ALLOWED_HOSTS = ['*']

STATIC_VERSION = os.getenv("STATIC_VERSION")
STATIC_URL = "/static/{}/".format(STATIC_VERSION)

FATHOM_KEY = os.getenv("FATHOM_KEY")
FATHOM_ANALYTICS_DOMAIN = os.getenv("FATHOM_ANALYTICS_DOMAIN")

if os.getenv("SENTRY_DNS", False):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DNS"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0,  # The Sentry plan does not include Performance.
    )

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "nasbdvn278ogurihlbkansbrb2uf")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "NO").lower() in ("on", "true", "y", "yes")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    },
    'kf_process': {
        "ENGINE": "django.db.backends.postgresql",
        'NAME': os.getenv("PROCESS_DB_NAME"),
        'USER': os.getenv("PROCESS_DB_USER"),
        'PASSWORD': os.getenv("PROCESS_DB_PASSWORD"),
        'HOST': os.getenv("PROCESS_DB_HOST"),
        'PORT': os.getenv("PROCESS_DB_PORT"),
    }
}

SCRAPY_HOST = os.getenv("SCRAPY_HOST")
SCRAPY_PROJECT = os.getenv("SCRAPY_PROJECT")
SCRAPY_FILES_STORE = os.getenv("SCRAPY_FILES_STORE")

PROCESS_HOST = os.getenv("PROCESS_HOST")
PELICAN_HOST = os.getenv("PELICAN_HOST")

EXPORTER_HOST = os.getenv("EXPORTER_HOST")
EXPORTER_DIR = os.getenv("EXPORTER_DIR")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "NO").lower() in ("on", "true", "y", "yes")
FEEDBACK_EMAIL = os.getenv("FEEDBACK_EMAIL")

RABBIT = {
    "host": os.getenv("RABBIT_HOST"),
    "port": os.getenv("RABBIT_PORT"),
    "username": os.getenv("RABBIT_USERNAME"),
    "password": os.getenv("RABBIT_PASSWORD"),
    "exchange_name": os.getenv("RABBIT_EXCHANGE_NAME")
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'data_registry': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'exporter': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'cbom': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'scrape-task': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}
