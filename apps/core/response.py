"""
Standardized response classes for API responses.
"""
from rest_framework.response import Response
from rest_framework import status


class StandardResponse(Response):
    """
    Custom Response class that inherits from DRF Response.
    Automatically formats responses with success, message, and data fields.
    
    Usage:
        return StandardResponse(data={'key': 'value'}, message='Success')
        return StandardResponse(data=None, message='Error', success=False, status_code=400)
    """
    
    def __init__(self, data=None, message='', success=True, status_code=None, **kwargs):
        """
        Initialize StandardResponse.
        
        Args:
            data: Response data (dict, list, or any serializable object)
            message: Response message
            success: Boolean indicating success (True) or error (False)
            status_code: HTTP status code (defaults based on success)
            **kwargs: Additional arguments passed to Response.__init__
        """
        if status_code is None:
            status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        
        response_data = {
            'success': success,
            'message': message,
            'data': data
        }
        
        super().__init__(data=response_data, status=status_code, **kwargs)
    
    @classmethod
    def success(cls, data=None, message='Success', status_code=status.HTTP_200_OK):
        """
        Create a successful response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            StandardResponse instance
        """
        return cls(data=data, message=message, success=True, status_code=status_code)
    
    @classmethod
    def error(cls, message='An error occurred', data=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Create an error response.
        
        Args:
            message: Error message
            data: Optional error data/details
            status_code: HTTP status code
            
        Returns:
            StandardResponse instance
        """
        return cls(data=data, message=message, success=False, status_code=status_code)
    
    @classmethod
    def created(cls, data=None, message='Resource created successfully'):
        """
        Create a 201 Created response.
        
        Args:
            data: Created resource data
            message: Success message
            
        Returns:
            StandardResponse instance
        """
        return cls(data=data, message=message, success=True, status_code=status.HTTP_201_CREATED)
    
    @classmethod
    def not_found(cls, message='Resource not found'):
        """
        Create a 404 Not Found response.
        
        Args:
            message: Error message
            
        Returns:
            StandardResponse instance
        """
        return cls(data=None, message=message, success=False, status_code=status.HTTP_404_NOT_FOUND)
    
    @classmethod
    def unauthorized(cls, message='Authentication required'):
        """
        Create a 401 Unauthorized response.
        
        Args:
            message: Error message
            
        Returns:
            StandardResponse instance
        """
        return cls(data=None, message=message, success=False, status_code=status.HTTP_401_UNAUTHORIZED)
    
    @classmethod
    def forbidden(cls, message='Permission denied'):
        """
        Create a 403 Forbidden response.
        
        Args:
            message: Error message
            
        Returns:
            StandardResponse instance
        """
        return cls(data=None, message=message, success=False, status_code=status.HTTP_403_FORBIDDEN)
    
    @classmethod
    def validation_error(cls, message='Validation failed', errors=None):
        """
        Create a 400 Bad Request response for validation errors.
        
        Args:
            message: Error message
            errors: Validation error details
            
        Returns:
            StandardResponse instance
        """
        return cls(data={'errors': errors} if errors else None, message=message, success=False, status_code=status.HTTP_400_BAD_REQUEST)
    
    @classmethod
    def server_error(cls, message='Internal server error'):
        """
        Create a 500 Internal Server Error response.
        
        Args:
            message: Error message
            
        Returns:
            StandardResponse instance
        """
        return cls(data=None, message=message, success=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

