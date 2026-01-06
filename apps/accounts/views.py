"""
Views for the accounts app.
"""
import logging
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from apps.core.response import StandardResponse
from apps.core.mixins import StandardResponseRetrieveMixin
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)
from .services.user_service import UserService

logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        summary='Register a new user',
        description='Create a new user account. Returns an authentication token upon successful registration.',
        request=UserRegistrationSerializer,
        responses={
            201: {'description': 'User created successfully'},
            400: {'description': 'Invalid input data'}
        },
        tags=['Auth'],
        examples=[
            OpenApiExample(
                'Example Registration',
                value={
                    'username': 'nathan-yinka',
                    'email': 'oludarenathaniel@gmail.com',
                    'password': '12345',
                    'password_confirm': '12345'
                },
                request_only=True,
            ),
        ]
    )
)
class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.
    Creates a new user account and returns an authentication token.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info(f'Registration attempt for email: {request.data.get("email", "unknown")}')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = UserService.register_user(serializer)
        return StandardResponse.created(
            data={
                'token': token.key,
                'user': UserService.get_user_data(user)
            },
            message='User registered successfully'
        )


@extend_schema_view(
    post=extend_schema(
        summary='User login',
        description='Authenticate user with email and password. Returns an authentication token upon successful login.',
        request=UserLoginSerializer,
        responses={
            200: {'description': 'Login successful'},
            400: {'description': 'Invalid credentials'}
        },
        tags=['Auth'],
        examples=[
            OpenApiExample(
                'Example Login',
                value={
                    'email': 'oludarenathaniel@gmail.com',
                    'password': '12345'
                },
                request_only=True,
            ),
        ]
    )
)
class UserLoginView(generics.GenericAPIView):
    """
    User login endpoint.
    Authenticates user and returns an authentication token.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        logger.info(f'Login attempt for email: {request.data.get("email", "unknown")}')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = UserService.login_user(user)
        return StandardResponse.success(
            data={
                'token': token.key,
                'user': UserService.get_user_data(user)
            },
            message='Login successful'
        )


class UserProfileView(StandardResponseRetrieveMixin, generics.RetrieveUpdateAPIView):
    """
    User profile endpoint.
    Allows authenticated users to view and update their profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    success_message = 'Profile retrieved successfully'

    @extend_schema(
        summary='Get user profile',
        description='Retrieve the authenticated user\'s profile information.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication required'}
        },
        tags=['User Profile']
    )

    @extend_schema(
        summary='Update user profile',
        description='Update the authenticated user\'s profile information.',
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {'description': 'Invalid input data'},
            401: {'description': 'Authentication required'}
        },
        tags=['User Profile']
    )
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        
        try:
            updated_user = UserService.update_user_profile(
                request.user,
                username=username,
                email=email
            )
            return StandardResponse.success(
                data=UserService.get_user_data(updated_user),
                message='Profile updated successfully'
            )
        except ValueError as e:
            return StandardResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary='Partially update user profile',
        description='Partially update the authenticated user\'s profile information.',
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {'description': 'Invalid input data'},
            401: {'description': 'Authentication required'}
        },
        tags=['User Profile']
    )
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        
        try:
            updated_user = UserService.update_user_profile(
                request.user,
                username=username,
                email=email
            )
            return StandardResponse.success(
                data=UserService.get_user_data(updated_user),
                message='Profile updated successfully'
            )
        except ValueError as e:
            return StandardResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

    def get_object(self):
        return self.request.user


class UserMeView(generics.RetrieveAPIView):
    """Current user endpoint."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Get current user',
        description='Retrieve the authenticated user\'s information.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication required'}
        },
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return StandardResponse.success(
            data=serializer.data,
            message='User information retrieved successfully'
        )


class UserLogoutView(APIView):
    """
    User logout endpoint.
    Blacklists the authentication token so it can no longer be used.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Logout user',
        description='Logout the authenticated user and blacklist their authentication token.',
        request=None,
        responses={
            200: {
                'description': 'Logout successful',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Logout successful',
                            'data': None
                        }
                    }
                }
            },
            400: {
                'description': 'Invalid token or logout failed',
                'content': {
                    'application/json': {
                        'example': {
                            'success': False,
                            'message': 'Invalid token',
                            'data': None
                        }
                    }
                }
            },
            401: {'description': 'Authentication required'}
        },
        tags=['Auth']
    )
    def post(self, request, *args, **kwargs):
        logger.info(f'Logout attempt for user: {request.user.email}')
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        success, message = UserService.logout_user(auth_header, request.user)
        
        if success:
            return StandardResponse.success(message=message)
        else:
            return StandardResponse.error(
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST
            )

