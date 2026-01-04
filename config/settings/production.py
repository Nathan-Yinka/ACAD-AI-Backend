"""
Production settings for acad_ai_assessment project.
"""
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]

if not ALLOWED_HOSTS:
    raise ValueError('ALLOWED_HOSTS environment variable must be set in production')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY environment variable must be set in production')

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if os.getenv('DATABASE_URL'):
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.parse(os.getenv('DATABASE_URL'))
    except ImportError:
        import warnings
        warnings.warn(
            'dj-database-url is not installed. Install it with: pip install dj-database-url',
            ImportWarning
        )

STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise configuration for serving static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING['handlers']['console']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['apps.accounts']['level'] = 'INFO'
LOGGING['loggers']['apps.assessments']['level'] = 'INFO'
LOGGING['loggers']['apps.core']['level'] = 'INFO'
LOGGING['root']['level'] = 'INFO'

