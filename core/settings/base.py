import os
from pathlib import Path

import dj_database_url
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+z4+npbj&h=hfaipwp!7$9r(s=ui9=e=b9dp7vt@g08mu8%a8x'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "NO").lower() in ("on", "true", "y", "yes")

ALLOWED_HOSTS = []

JOB_TASKS_PLAN = ["scrape", "process", "pelican", "exporter"]

EXPORTER_DIR = "exporter_dumps"
EXPORTER_PAGE_SIZE = 10000

FEEDBACK_EMAIL = "noreply@noreply.open-contracting.org"
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Application definition

INSTALLED_APPS = [
    'data_registry',
    'modeltranslation',
    'core.apps.CoreAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'markdownx',
    'exporter'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'core.context_processors.from_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql:///data_registry?application_name=data_registry'),
    'kingfisher_process': dj_database_url.config(
        env='KINGFISHER_PROCESS_DATABASE_URL',
        default='postgresql:///kingfisher_process?application_name=kingfisher_process'),
}

FLATTEN_URL = "https://flatten.open-contracting.org/api/urls/"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = 'data_registry/static/'
STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('ru', _('Russian')),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'data_registry', 'locale'),
]

MARKDOWNX_MARKDOWNIFY_FUNCTION = 'data_registry.utils.markdownify'

SCRAPY_HOST = os.getenv("SCRAPY_HOST")
SCRAPY_PROJECT = os.getenv("SCRAPY_PROJECT")

EXPORTER_HOST = os.getenv("EXPORTER_HOST")

SPOONBILL_API_USERNAME = os.getenv("SPOONBILL_API_USERNAME")
SPOONBILL_API_PASSWORD = os.getenv("SPOONBILL_API_PASSWORD")
