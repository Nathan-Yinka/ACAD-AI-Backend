"""Tests for accounts models."""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the User model."""

    def test_create_user_with_email(self):
        """Test creating a user with email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            username='testuser',
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com', 'user1'],
            ['Test2@Example.com', 'Test2@example.com', 'user2'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com', 'user3'],
        ]
        for email, expected, username in sample_emails:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='sample123'
            )
            self.assertEqual(user.email, expected)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_user_is_student_default(self):
        """Test user is_student defaults to True."""
        user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='test123'
        )
        self.assertTrue(user.is_student)
