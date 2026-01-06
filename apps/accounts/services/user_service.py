"""Service for handling user operations."""
import logging
from typing import Tuple, Optional
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from apps.accounts.models import User, BlacklistedToken
from apps.accounts.serializers import UserRegistrationSerializer, UserSerializer

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic."""
    
    @staticmethod
    def register_user(serializer: UserRegistrationSerializer) -> Tuple[User, Token]:
        """
        Register a new user and create authentication token.
        
        Args:
            serializer: Validated UserRegistrationSerializer instance
            
        Returns:
            Tuple of (user, token)
        """
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f'User {user.email} registered successfully')
        return user, token
    
    @staticmethod
    def login_user(user: User) -> Token:
        """
        Get or create authentication token for authenticated user.
        
        Args:
            user: Authenticated user instance (already validated by serializer)
            
        Returns:
            Token instance
        """
        token, created = Token.objects.get_or_create(user=user)
        logger.info(f'User {user.email} logged in successfully')
        return token
    
    @staticmethod
    def logout_user(auth_header: str, user: User) -> Tuple[bool, str]:
        """
        Logout user by blacklisting token.
        
        Args:
            auth_header: HTTP Authorization header value
            user: Current authenticated user
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not auth_header.startswith('Bearer '):
            return False, 'Authorization header missing or invalid'
        
        token_key = auth_header.split(' ')[1]
        
        try:
            token = Token.objects.get(key=token_key)
            BlacklistedToken.objects.get_or_create(
                token=token_key,
                defaults={'user': user}
            )
            token.delete()
            logger.info(f'User {user.email} logged out successfully. Token blacklisted.')
            return True, 'Logout successful'
        except Token.DoesNotExist:
            logger.warning(f'Token not found for user: {user.email}')
            return False, 'Invalid token'
    
    @staticmethod
    def get_user_data(user: User) -> dict:
        """
        Get serialized user data.
        
        Args:
            user: User instance
            
        Returns:
            Serialized user data
        """
        return UserSerializer(user).data

    @staticmethod
    def validate_profile_update(user: User, username: str = None, email: str = None) -> Tuple[bool, str]:
        """
        Validate that username and email are not already taken by another user.
        
        Args:
            user: Current user instance
            username: New username to validate (optional)
            email: New email to validate (optional)
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if username is not None:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return False, 'Username is already taken.'
        
        if email is not None:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return False, 'Email is already taken.'
        
        return True, ''

    @staticmethod
    def update_user_profile(user: User, username: str = None, email: str = None) -> User:
        """
        Update user profile with validation.
        
        Args:
            user: User instance to update
            username: New username (optional)
            email: New email (optional)
            
        Returns:
            Updated user instance
            
        Raises:
            ValueError: If username or email is already taken
        """
        is_valid, error_message = UserService.validate_profile_update(user, username, email)
        if not is_valid:
            raise ValueError(error_message)
        
        update_fields = []
        if username is not None:
            user.username = username
            update_fields.append('username')
        if email is not None:
            user.email = email
            update_fields.append('email')
        
        if update_fields:
            user.save(update_fields=update_fields)
            logger.info(f'User {user.email} profile updated successfully')
        
        return user

