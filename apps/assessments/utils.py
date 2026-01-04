"""
Utility functions for the assessments app.
"""
from datetime import timedelta
from django.utils import timezone


def calculate_exam_deadline(start_time, duration_minutes):
    """
    Calculate the deadline for an exam based on start time and duration.
    
    Args:
        start_time: Datetime when the exam was started
        duration_minutes: Duration of the exam in minutes
        
    Returns:
        Datetime representing the exam deadline
    """
    return start_time + timedelta(minutes=duration_minutes)


def is_exam_time_exceeded(start_time, duration_minutes):
    """
    Check if the exam time limit has been exceeded.
    
    Args:
        start_time: Datetime when the exam was started
        duration_minutes: Duration of the exam in minutes
        
    Returns:
        Boolean indicating if time limit is exceeded
    """
    deadline = calculate_exam_deadline(start_time, duration_minutes)
    return timezone.now() > deadline

