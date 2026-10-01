###################################################################
#  This file serves as a base configuration for testing purposes  #
#  only. It is not intended for production use.                   #
###################################################################

ALLOWED_HOSTS = ['*']

DATABASE = {
    'NAME': 'netbox',
    'USER': 'postgres',
    'PASSWORD': 'postgres',
    'HOST': 'localhost',
    'PORT': '',
    'CONN_MAX_AGE': 300,
}

PLUGINS = [
    'sidekick',
]

REDIS = {
    'tasks': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'DATABASE': 0,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'DATABASE': 1,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    }
}

SECRET_KEY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

# NetBox 4.x creates v2 API tokens by default, and creating one requires at
# least one pepper of 50+ characters. Without this, any test that calls
# Token.objects.create() fails with "API_TOKEN_PEPPERS is not defined".
API_TOKEN_PEPPERS = {
    1: 'sidekick-test-pepper-not-a-secret-0123456789-abcdefghij',
}
