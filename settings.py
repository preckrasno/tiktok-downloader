from decouple import config

API_TOKEN = config('API_TOKEN',default=False)
SENTRY_DSN = config('SENTRY_DSN',default=False)
ENVIRONMENT = config('ENVIRONMENT', default='Local')
USER_AGENT = config('USER_AGENT',default=False)
GITHUB_API_URL = config('GITHUB_API_URL',default=False)
GITHUB_API_TOKEN = config('GITHUB_API_TOKEN',default=False)
GITHUB_API_USER_NAME = config('GITHUB_API_USER_NAME',default=False, cast=str)
GITHUB_API_USER_EMAIL = config('GITHUB_API_USER_EMAIL',default=False, cast=str)
