import os

import dj_database_url
from django.contrib.postgres import fields  # noqa: F403,F401

from .base import *  # noqa: F403,F401

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '^0z5u6!dsdafsdf52345jknosk5k!uf-6n_0#2*p_4')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    # https://docs.djangoproject.com/en/3.0/ref/databases/#postgresql-connection-settings
    'default': dj_database_url.config(
        default='postgresql:///data_registry?application_name=data_registry'),
}


# The schema in the older version had index names longer than 30 characters.
SILENCED_SYSTEM_CHECKS = [
    'models.E034',
]

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
        'worker': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}
