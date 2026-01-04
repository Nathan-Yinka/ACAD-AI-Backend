"""
App configuration for assessments app.
"""
from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    """
    Configuration for the assessments application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessments'
    verbose_name = 'Assessments'

