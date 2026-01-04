"""WebSocket consumers for exam session events."""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class ExamSessionConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time exam session events."""

    async def connect(self):
        """Handle WebSocket connection using session token."""
        self.session_token = self.scope['url_route']['kwargs']['token']
        self.room_group_name = f'exam_session_{self.session_token}'
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4003)
            return

        # Check token validity
        is_valid, reason = await self.check_token_validity()
        
        if not is_valid:
            await self.accept()
            event_type, message = self._get_event_for_reason(reason)
            await self.send(text_data=json.dumps({
                'type': event_type,
                'message': message,
                'reason': reason,
            }))
            await self.close(code=4001)
            return

        # Verify token belongs to user
        session_data = await self.get_session_data()
        if not session_data or session_data['student_id'] != self.user.id:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'time_remaining_seconds': session_data['time_remaining'],
            'answered_count': session_data['answered_count'],
            'total_questions': session_data['total_questions'],
        }))

    def _get_event_for_reason(self, reason):
        """Get event type and message based on reason."""
        if reason == 'token_expired':
            return 'session_expired', 'This session token has expired. A new session was started.'
        elif reason == 'invalid_token':
            return 'session_expired', 'Invalid session token.'
        elif reason == 'session_completed':
            return 'session_completed', 'This exam has already been submitted.'
        elif reason == 'session_timeout':
            return 'session_completed', 'Exam time has ended.'
        else:
            return 'session_expired', 'Session is no longer valid.'

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                is_valid, reason = await self.check_token_validity()
                if is_valid:
                    session_data = await self.get_session_data()
                    await self.send(text_data=json.dumps({
                        'type': 'pong',
                        'time_remaining_seconds': session_data['time_remaining'],
                        'answered_count': session_data['answered_count'],
                    }))
                else:
                    event_type, message = self._get_event_for_reason(reason)
                    await self.send(text_data=json.dumps({
                        'type': event_type,
                        'message': message,
                        'reason': reason,
                    }))
        except json.JSONDecodeError:
            pass

    async def session_completed(self, event):
        """Handle session completed event (timeout or manual submit)."""
        await self.send(text_data=json.dumps({
            'type': 'session_completed',
            'message': event['message'],
            'reason': event.get('reason', 'submitted'),
            'grade_history_id': event.get('grade_history_id'),
        }))

    async def session_expired(self, event):
        """Handle session expired event (token invalidated by new session)."""
        await self.send(text_data=json.dumps({
            'type': 'session_expired',
            'message': event['message'],
            'reason': event.get('reason', 'token_expired'),
        }))

    @database_sync_to_async
    def check_token_validity(self):
        """Check if token is still valid."""
        from apps.assessments.services.exam_session_service import ExamSessionService
        return ExamSessionService.check_token_validity(self.session_token)

    @database_sync_to_async
    def get_session_data(self):
        """Get session data for the token."""
        from apps.assessments.models import SessionToken
        try:
            token_obj = SessionToken.objects.select_related(
                'session', 'session__exam'
            ).get(token=self.session_token)
            session = token_obj.session
            return {
                'student_id': session.student_id,
                'time_remaining': session.time_remaining_seconds(),
                'answered_count': session.get_answered_count(),
                'total_questions': session.get_total_questions(),
            }
        except SessionToken.DoesNotExist:
            return None
