"""
User model for the accounts app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_student']),
        ]

    def __str__(self):
        return self.email


class BlacklistedToken(models.Model):
    """
    Model to store blacklisted authentication tokens.
    """
    token = models.CharField(max_length=40, unique=True, db_index=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'blacklisted_tokens'
        verbose_name = 'Blacklisted Token'
        verbose_name_plural = 'Blacklisted Tokens'
        ordering = ['-blacklisted_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['blacklisted_at']),
        ]

    def __str__(self):
        return f'Blacklisted token: {self.token[:10]}...'
