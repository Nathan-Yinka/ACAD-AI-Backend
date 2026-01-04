"""
Logging configuration for the application.
"""
import logging
import os
from pathlib import Path


def get_logging_config(base_dir):
    """
    Get logging configuration dictionary for Django.
    
    Args:
        base_dir: Base directory path (Path object)
        
    Returns:
        dict: Django LOGGING configuration
    """
    LOG_DIR = base_dir / 'logs'
    LOG_DIR.mkdir(exist_ok=True)
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {asctime} {message}',
                'style': '{',
            },
            'json': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'django.log',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'errors.log',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 5,
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['error_file'],
                'level': 'ERROR',
                'propagate': False,
            },
            'apps.accounts': {
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'apps.assessments': {
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
            'apps.core': {
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
        },
    }
    
    return LOGGING_CONFIG


def setup_logging():
    """
    Configure logging for the application.
    Deprecated: Use get_logging_config() instead.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    return get_logging_config(BASE_DIR)


def get_logger(name):
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

