# In production set the environment variable like this:
#    DJANGO_SETTINGS_MODULE=HomeAutomation.settings.production
import logging.config
import os

from .base import *  # NOQA


# For security and performance reasons, DEBUG is turned off
DEBUG = False
TEMPLATE_DEBUG = False



# Must mention ALLOWED_HOSTS in production!
ALLOWED_HOSTS = ["mizamae2.ddns.net","192.168.0.160","127.0.0.1"]


MIGRATION_MODULES={
        'HomeAutomation':'HomeAutomation.migrations',
    }

# Cache the templates in memory for speed-up
loaders = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

TEMPLATES[0]['OPTIONS'].update({"loaders": loaders})
TEMPLATES[0].update({"APP_DIRS": False})

# Define STATIC_ROOT for the collectstatic command
STATIC_ROOT = join(BASE_DIR, '..', 'site', 'static')

#CHANNELS CONFIGURATION
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT=6379
# Channel layer definitions
# http://channels.readthedocs.org/en/latest/deploying.html#setting-up-a-channel-backend
CHANNEL_LAYERS = {
    "default": {
        # This example app uses the Redis channel layer implementation asgi_redis
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
        "ROUTING": "HomeAutomation.routing.channel_routing",
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': join(BASE_DIR, '..', '..', 'run','django-cache')#'/home/pi/run/django-cache',
    }
}

# Log everything to the logs directory at the top
LOGFILE_ROOT = join(BASE_DIR, '..', 'logs') #'/home/pi/HomeAutomation/logs'

# Reset logging
LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'django_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join(LOGFILE_ROOT, 'django.log'),
            'maxBytes': 1000000,
            'backupCount': 1,
            'formatter': 'verbose'
        },
        'proj_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join(LOGFILE_ROOT, 'project.log'),
            'maxBytes': 100000,
            'backupCount': 1,
            'formatter': 'verbose'
        },
        'proc_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join(LOGFILE_ROOT, 'processes.log'),
            'maxBytes': 10000,
            'backupCount': 0,
            'formatter': 'verbose'
        },
        'scheduler_log_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join(LOGFILE_ROOT, 'scheduler.log'),
            'maxBytes': 10000,
            'backupCount': 0,
            'formatter': 'verbose'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['django_log_file'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'project': {
            'handlers': ['proj_log_file'],
            'level': 'DEBUG',
        },
        'processes': {
            'handlers': ['proc_log_file'],
            'level': 'DEBUG',
        },
        'apscheduler.scheduler':{
            'handlers': ['scheduler_log_file'],
            'level': 'DEBUG',
        }
    }
}

logging.config.dictConfig(LOGGING)
