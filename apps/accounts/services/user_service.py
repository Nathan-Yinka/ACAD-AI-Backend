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

