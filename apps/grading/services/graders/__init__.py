"""Grading algorithms package."""
from .base import BaseGradingService
from .mock_grading import MockGradingService
from .llm_grading import LLMGradingService
from django.conf import settings


def get_grading_service():
    """Factory function to get the appropriate grading service based on settings."""
    grading_service_type = getattr(settings, 'GRADING_SERVICE', 'mock')
    
    if grading_service_type == 'llm':
        return LLMGradingService()
    else:
        return MockGradingService()

