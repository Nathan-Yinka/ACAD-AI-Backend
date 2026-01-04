"""WebSocket URL routing for assessments app."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/exam/(?P<token>[\w-]+)/?$', consumers.ExamSessionConsumer.as_asgi()),
]
