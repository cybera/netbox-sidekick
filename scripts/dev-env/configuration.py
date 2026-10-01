"""Test-only NetBox configuration for the sidekick dev/CI container.

Loaded by scripts/dev-env/Dockerfile. The database and Redis hostnames match
the container aliases created by scripts/dev-env/run-tests.sh. Nothing here is
a real secret: this configuration is never used outside a throwaway container.
"""

ALLOWED_HOSTS = ['*']

DATABASE = {
    'NAME': 'netbox',
    'USER': 'postgres',
    'PASSWORD': 'postgres',
    'HOST': 'pg',
    'PORT': '5432',
    'CONN_MAX_AGE': 300,
}

PLUGINS = [
    'sidekick',
]

REDIS = {
    'tasks': {
        'HOST': 'redis',
        'PORT': 6379,
        'PASSWORD': '',
        'DATABASE': 0,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
    'caching': {
        'HOST': 'redis',
        'PORT': 6379,
        'PASSWORD': '',
        'DATABASE': 1,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
}

# NetBox 4.x creates v2 API tokens, which require a pepper. Without this,
# Token.objects.create() raises "API_TOKEN_PEPPERS is not defined".
API_TOKEN_PEPPERS = {
    1: 'sidekick-test-pepper-not-a-secret-0123456789-abcdefghij',
}

SECRET_KEY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
