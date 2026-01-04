"""
Mixin classes for ViewSets and API views.
"""
from rest_framework.response import Response
from .response import StandardResponse


class StandardResponseMixin:
    """Mixin that automatically wraps ViewSet responses in standardized format."""
    
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        
        if isinstance(response, Response) and response.status_code < 400:
            if isinstance(response.data, dict) and 'success' in response.data:
                return response
            
            standard_response = StandardResponse(
                data=response.data,
                message=self._get_success_message(),
                success=True,
                status_code=response.status_code
            )
            response.data = standard_response.data
        
        return response
    
    def _get_success_message(self):
        action = getattr(self, 'action', None)
        action_messages = {
            'list': f'{self._get_model_name()}s retrieved successfully',
            'retrieve': f'{self._get_model_name()} retrieved successfully',
            'create': f'{self._get_model_name()} created successfully',
            'update': f'{self._get_model_name()} updated successfully',
            'partial_update': f'{self._get_model_name()} updated successfully',
            'destroy': f'{self._get_model_name()} deleted successfully',
            'submit': 'Submission created and graded successfully',
        }
        return action_messages.get(action, 'Operation completed successfully')
    
    def _get_model_name(self):
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model._meta.verbose_name.title()
        elif hasattr(self, 'serializer_class') and self.serializer_class is not None:
            meta = getattr(self.serializer_class, 'Meta', None)
            if meta and hasattr(meta, 'model'):
                return meta.model._meta.verbose_name.title()
        return 'Resource'

