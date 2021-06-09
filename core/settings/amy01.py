from .base import *  # noqa: F403,F401

ENVIRONMENT = "development"

STATIC_VERSION = "v1"
STATIC_URL = "/static/{}/".format(STATIC_VERSION)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x_ayh_$*yjafdafdsdfuh4jjsdfgvy536-g#gjes#4&4*yp%7li94n^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'data_registry',
        'USER': 'data_registry',
        'PASSWORD': 'mnabisadnf7g9y24589thkadv',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
    'kf_process': {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "kingfisher",
        "USER": "kingfisher",
        "PASSWORD": "kingfisher",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

SCRAPY_HOST = "http://localhost:6800/"
SCRAPY_PROJECT = "kingfisher"

PROCESS_HOST = "http://localhost:8000/"

PELICAN_HOST = "http://localhost:8001/"

EXPORTER_HOST = "https://data-registry.datlab.eu/"

EXPORTER_DIR = "/data/exporter_dumps"

RABBIT = {
    "host": "localhost",
    "port": "5672",
    "username": "rabbit",
    "password": "rabbit",
    "exchange_name": "data-registry_production",
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
        }
    }
}
