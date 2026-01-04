"""Tests for accounts views."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class AuthenticationTests(TestCase):
    """Tests for authentication endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_register_user_success(self):
        """Test user registration is successful."""
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email."""
        User.objects.create_user(
            username='existing',
            email=self.user_data['email'],
            password='other123'
        )
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_invalid_email(self):
        """Test registration fails with invalid email."""
        self.user_data['email'] = 'invalid-email'
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        self.user_data['password_confirm'] = 'DifferentPass123!'
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test login is successful."""
        User.objects.create_user(
            username='testuser',
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        User.objects.create_user(
            username='testuser',
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login fails for nonexistent user."""
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTests(TestCase):
    """Tests for user profile endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        self.profile_url = reverse('accounts:profile')

    def test_get_profile_success(self):
        """Test retrieving profile is successful."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], self.user.email)

    def test_get_profile_unauthenticated(self):
        """Test profile requires authentication."""
        self.client.credentials()  # Remove credentials
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_success(self):
        """Test updating profile is successful."""
        response = self.client.patch(self.profile_url, {
            'username': self.user.username  # Required field
        })

        # Check that update was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
