"""
URL configuration for the accounts app.
"""
from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserProfileView, UserMeView

app_name = 'accounts'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('me/', UserMeView.as_view(), name='me'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]

