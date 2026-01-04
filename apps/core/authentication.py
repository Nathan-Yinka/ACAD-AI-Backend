"""
Custom authentication classes for the application.
"""
from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """
    Token authentication using Bearer prefix instead of Token.
    Clients should send: Authorization: Bearer <token>
    """
    keyword = 'Bearer'

