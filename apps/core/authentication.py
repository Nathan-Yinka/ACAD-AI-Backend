"""
Custom authentication classes for the application.
"""
from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """
    Token authentication using Bearer prefix instead of Token.
    Clients should send: Authorization: Bearer <token>
    Checks for blacklisted tokens before authenticating.
    """
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        """Override to check if token is blacklisted before authenticating."""
        try:
            from apps.accounts.models import BlacklistedToken
            BlacklistedToken.objects.get(token=key)
            from rest_framework import exceptions
            raise exceptions.AuthenticationFailed('Session has expired, login again')
        except BlacklistedToken.DoesNotExist:
            pass
        
        return super().authenticate_credentials(key)

