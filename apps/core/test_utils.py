"""Test utilities and helper functions."""
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


def create_test_user(email='test@example.com', password='testpass123', **kwargs):
    """Create a test user with auto-generated username."""
    username = kwargs.pop('username', email.split('@')[0] + '_' + str(uuid.uuid4())[:8])
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        **kwargs
    )


def create_test_admin(email='admin@example.com', password='admin123', **kwargs):
    """Create a test admin/superuser with auto-generated username and is_student=False."""
    username = kwargs.pop('username', 'admin_' + str(uuid.uuid4())[:8])
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        **kwargs
    )
    # Admins should not be students
    user.is_student = False
    user.save()
    return user


def create_test_user_with_token(email='test@example.com', password='testpass123', **kwargs):
    """Create a test user and return user with token using UserService."""
    from apps.accounts.services.user_service import UserService
    user = create_test_user(email, password, **kwargs)
    token = UserService.login_user(user)
    return user, token


def create_test_admin_with_token(email='admin@example.com', password='admin123', **kwargs):
    """Create a test admin user and return user with token using UserService."""
    from apps.accounts.services.user_service import UserService
    user = create_test_admin(email, password, **kwargs)
    token = UserService.login_user(user)
    return user, token

