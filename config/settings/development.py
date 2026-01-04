"""
Development settings for acad_ai_assessment project.
"""
import sys
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Flag to indicate testing mode (disables Celery task scheduling)
TESTING = 'test' in sys.argv

# django_extensions provides useful development-only tools:
# - shell_plus: Enhanced Django shell with auto-imports
# - runserver_plus: Enhanced runserver with Werkzeug debugger
# - graph_models: Generate model relationship diagrams
# - show_urls: Display all URL patterns
# - create_jobs: Create management command templates
# Only loaded in development, not needed in production
try:
    import django_extensions
    INSTALLED_APPS += [
        'django_extensions',
    ]
except ImportError:
    # django_extensions is optional - install with: pip install django-extensions
    pass

