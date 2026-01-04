"""
Views for the accounts app.
"""
import logging
from rest_framework import status, generics, permissions
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from apps.core.response import StandardResponse
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)

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
                    'password_confirm': '12345',
                    'is_student': True
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
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f'User {user.email} registered successfully')
        return StandardResponse.created(
            data={
                'token': token.key,
                'user': UserSerializer(user).data
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
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f'User {user.email} logged in successfully')
        return StandardResponse.success(
            data={
                'token': token.key,
                'user': UserSerializer(user).data
            },
            message='Login successful'
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile endpoint.
    Allows authenticated users to view and update their profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Get user profile',
        description='Retrieve the authenticated user\'s profile information.',
        responses={
            200: UserSerializer,
            401: {'description': 'Authentication required'}
        },
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Profile retrieved successfully'
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
        response = super().put(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return StandardResponse.success(
                data=response.data,
                message='Profile updated successfully'
            )
        return response

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
        response = super().patch(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            return StandardResponse.success(
                data=response.data,
                message='Profile updated successfully'
            )
        return response

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

