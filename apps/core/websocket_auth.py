"""WebSocket authentication middleware for token-based auth."""
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_token(token_key):
    """Get user from token key."""
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """WebSocket middleware for token authentication."""
    
    async def __call__(self, scope, receive, send):
        """Authenticate user from token in query string."""
        if scope['type'] == 'websocket':
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            
            token_key = None
            if 'token' in query_params:
                token_key = query_params['token'][0]
            
            if token_key:
                scope['user'] = await get_user_from_token(token_key)
            else:
                scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    """Stack token auth middleware."""
    return TokenAuthMiddleware(inner)

