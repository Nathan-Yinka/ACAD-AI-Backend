"""
Mixin classes for ViewSets and API views.
"""
from django.http import Http404
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .response import StandardResponse


class BaseMixin:
    """Base mixin class that all mixins inherit from."""
    
    def _get_model_name(self):
        """Extract model name from serializer or queryset."""
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model._meta.verbose_name.title()
        elif hasattr(self, 'serializer_class') and self.serializer_class is not None:
            meta = getattr(self.serializer_class, 'Meta', None)
            if meta and hasattr(meta, 'model'):
                return meta.model._meta.verbose_name.title()
        return 'Resource'


class StandardResponseMixin(BaseMixin):
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


class Custom404Mixin(BaseMixin):
    """Mixin that provides custom 404 messages for get_object() method."""
    
    not_found_message = 'Resource not found.'
    
    def get_object(self):
        """Override to provide custom 404 message."""
        try:
            return super().get_object()
        except Http404:
            raise NotFound(self.not_found_message)


class StandardResponseGenericMixin(BaseMixin):
    """Base mixin for StandardResponse wrapping of generic API views."""
    
    success_message = None
    
    def get(self, request, *args, **kwargs):
        """Override get() to wrap response in StandardResponse format."""
        response = super().get(request, *args, **kwargs)
        message = self.success_message or self._get_default_message()
        return StandardResponse.success(
            data=response.data,
            message=message
        )
    
    def _get_default_message(self):
        """Override in subclasses to provide default message."""
        raise NotImplementedError("Subclasses must implement _get_default_message()")


class StandardResponseListMixin(StandardResponseGenericMixin):
    """Mixin that auto-wraps ListAPIView responses in StandardResponse format."""
    
    def _get_default_message(self):
        """Auto-generate message from serializer/model name."""
        model_name = self._get_model_name()
        return f'{model_name}s retrieved successfully'


class StandardResponseRetrieveMixin(StandardResponseGenericMixin):
    """Mixin that auto-wraps RetrieveAPIView responses in StandardResponse format."""
    
    def _get_default_message(self):
        """Auto-generate message from serializer/model name."""
        model_name = self._get_model_name()
        return f'{model_name} retrieved successfully'

