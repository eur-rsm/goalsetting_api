import os
import socket

from dotenv import load_dotenv
from corsheaders.defaults import default_headers

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'TODO'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'background_task',

    'core.apps.CoreConfig',
    'chat',
    'demo',
    'api.apps.ApiConfig',
    'tasks.apps.TasksConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oidc_auth.authentication.JSONWebTokenAuthentication',
        'oidc_auth.authentication.BearerTokenAuthentication',
    ),
}

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
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '{asctime} {levelname:8} {origin:20} {message}',
            'style': '{',
        }
    },

    'handlers': {
        'app': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './_log/app.log',
            'formatter': 'default'
        },

        'debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': './_log/debug.log',
            'formatter': 'default'
        },
        # Not actual loggers, only used for the file locations
        'chat': {
            'class': 'logging.FileHandler',
            'filename': './_log/chat/default.log',
        },
    },
    'loggers': {
        'app': {
            'handlers': ['app'],
            'level': 'INFO',
            'propagate': True,
        },

        'debug': {
            'handlers': ['debug'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

os.makedirs('./_log/chat/', exist_ok=True)

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

OIDC_AUTH = {
    # Specify OpenID Connect endpoint. Configuration will be
    # automatically done based on the discovery document found
    # at <endpoint>/.well-known/openid-configuration
    'OIDC_ENDPOINT': '<TODO>',

    # Accepted audiences the ID Tokens can be issued to
    'OIDC_AUDIENCES': ('<TODO>', ),

    # (Optional) Function that resolves id_token into user.
    # This function receives a request and an id_token dict and expects to
    # return a User object. The default implementation tries to find the user
    # based on username (natural key) taken from the 'sub'-claim of the
    # id_token.
    'OIDC_RESOLVE_USER_FUNCTION': 'core.oidc.get_user_by_sub',

    # (Optional) Number of seconds in the past valid tokens can be
    # issued (default 600)
    'OIDC_LEEWAY': 3600,

    # (Optional) Time before signing keys will be refreshed (default 24 hrs)
    'OIDC_JWKS_EXPIRATION_TIME': 24 * 60 * 60,

    # (Optional) Time before bearer token validity is verified again (default 10 minutes)
    'OIDC_BEARER_TOKEN_EXPIRATION_TIME': 10 * 60,

    # (Optional) Token prefix in JWT authorization header (default 'JWT')
    'JWT_AUTH_HEADER_PREFIX': 'JWT',

    # (Optional) Token prefix in Bearer authorization header (default 'Bearer')
    'BEARER_AUTH_HEADER_PREFIX': 'Bearer',

    # (Optional) Which Django cache to use
    # 'OIDC_CACHE_NAME': 'default',

    # (Optional) A cache key prefix when storing and retrieving cached values
    # 'OIDC_CACHE_PREFIX': 'oidc_auth.',
}

# Custom settings
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + ['Access-Token', ]

TASKS_CSV = 'tasks.csv'

# Chat settings
CHAT_MASTER = 'bot'
CHAT_MASTER_NAME = '<TODO>'
RASA_URL = 'http://localhost:{port}/webhooks/rest/webhook'
RASA_API = 'http://localhost:{port}/conversations/{username}/tracker/events'
ACTION_URL = 'http://localhost:{port}/webhook'

# OneSignal
USER_AUTH_KEY = '<TODO>'
APP_AUTH_KEY = '<TODO>'
APP_ID = '<TODO>'
# Update every 15 mins
REPEAT = 15 * 60
