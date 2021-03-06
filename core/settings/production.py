from .base import *  # noqa: F403,F401

ENVIRONMENT = "production"


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x_ayh_asdfsdfdsterwtefgewrtp%7li94n^'

FATHOM_KEY = "HTTGFPYH"
FATHOM_ANALYTICS_DOMAIN = 'cdn.usefathom.com'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'data_registry',
        'USER': 'data_registry',
        'PASSWORD': 'data_registry',
        'HOST': '127.0.0.1',
        'PORT': '22090',
    }
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
    }
}
