"""
Custom exception classes and handlers for the application.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework import status


class AssessmentException(APIException):
    """Base exception for assessment-related errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred processing your request.'
    default_code = 'assessment_error'


class ExamNotFoundError(AssessmentException):
    """Raised when an exam is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Exam not found.'
    default_code = 'exam_not_found'


class SubmissionValidationError(AssessmentException):
    """Raised when submission validation fails."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Submission validation failed.'
    default_code = 'submission_validation_error'


class GradingError(AssessmentException):
    """Raised when grading fails."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Grading failed. Please try again later.'
    default_code = 'grading_error'


class ExamModificationError(AssessmentException):
    """Raised when exam modification is not allowed."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Exam cannot be modified when it has active sessions or submissions.'
    default_code = 'exam_modification_error'


class TimeLimitExceededError(SubmissionValidationError):
    """Raised when exam time limit is exceeded."""
    default_detail = 'Exam time limit exceeded.'
    default_code = 'time_limit_exceeded'


class IncompleteSubmissionError(SubmissionValidationError):
    """Raised when submission is incomplete."""
    default_detail = 'Submission is incomplete. All questions must be answered.'
    default_code = 'incomplete_submission'


def custom_exception_handler(exc, context):
    """Custom exception handler that provides consistent error response format."""
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, 'default_code', 'error')
        error_message = str(exc)
        error_data = None
        
        if isinstance(exc, (ValidationError, AuthenticationFailed, NotAuthenticated)):
            errors = response.data if isinstance(response.data, dict) else {'error': response.data}
            if isinstance(errors, dict) and 'non_field_errors' in errors:
                errors['error'] = errors.pop('non_field_errors')
            error_data = {'errors': errors}
            
            if isinstance(response.data, dict):
                if 'non_field_errors' in response.data:
                    non_field_errors = response.data['non_field_errors']
                    if non_field_errors:
                        first_error = non_field_errors[0] if isinstance(non_field_errors, list) else non_field_errors
                        error_message = str(first_error) if not isinstance(first_error, dict) else first_error.get('message', str(first_error))
                elif 'detail' in response.data:
                    error_message = str(response.data['detail'])
                    error_data = {'errors': {'error': [error_message]}}
                elif len(response.data) == 1:
                    field_name, field_errors = next(iter(response.data.items()))
                    if isinstance(field_errors, list) and field_errors:
                        first_error = field_errors[0]
                        error_message = str(first_error) if not isinstance(first_error, dict) else first_error.get('message', str(first_error))
                    else:
                        error_message = str(field_errors) if not isinstance(field_errors, dict) else field_errors.get('message', str(field_errors))
                else:
                    error_message = 'Validation failed. Please check your input.'
            else:
                if isinstance(response.data, list) and response.data:
                    error_message = str(response.data[0])
                    error_data = {'errors': {'error': [error_message]}}
                else:
                    error_message = str(response.data) if response.data else 'Validation failed.'
                    error_data = {'errors': {'error': [error_message]}}
        elif isinstance(exc, PermissionDenied):
            error_message = str(exc) if hasattr(exc, 'detail') and exc.detail else 'You do not have permission to perform this action.'
            error_data = {'errors': {'error': [error_message]}}
        elif isinstance(response.data, dict):
            if 'detail' in response.data:
                error_message = str(response.data['detail'])
                error_data = {'errors': {'error': [error_message]}}
            else:
                if 'message' in response.data:
                    error_message = str(response.data['message'])
                    error_data = {'errors': response.data}
                else:
                    error_data = {'errors': response.data}
        else:
            error_message = str(response.data) if response.data else str(exc)
            error_data = {'errors': {'error': [error_message]}}
        
        custom_response_data = {
            'success': False,
            'message': error_message,
            'data': error_data
        }
        
        response.data = custom_response_data

    return response

