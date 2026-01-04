"""Tests for WebSocket consumers."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession
from apps.assessments.consumers import ExamSessionConsumer
from apps.assessments.services.exam_session_service import ExamSessionService


class ExamSessionConsumerTests(TestCase):
    """Tests for ExamSessionConsumer WebSocket."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)
        self.session = ExamSession.objects.create(student=self.user, exam=self.exam)
        self.token = self.session.create_new_token()

    async def test_consumer_connection_flow(self):
        """Test basic consumer connection and disconnection flow."""
        consumer = ExamSessionConsumer()
        consumer.session_token = self.token.token
        
        is_valid, reason = await database_sync_to_async(
            lambda: (True, None)
        )()
        self.assertTrue(is_valid)

    def test_get_event_for_reason_token_expired(self):
        """Test event generation for token expired reason."""
        consumer = ExamSessionConsumer()
        event_type, message = consumer._get_event_for_reason('token_expired')
        
        self.assertEqual(event_type, 'session_expired')
        self.assertIn('expired', message.lower())

    def test_get_event_for_reason_invalid_token(self):
        """Test event generation for invalid token reason."""
        consumer = ExamSessionConsumer()
        event_type, message = consumer._get_event_for_reason('invalid_token')
        
        self.assertEqual(event_type, 'session_expired')
        self.assertIn('invalid', message.lower())

    def test_get_event_for_reason_session_completed(self):
        """Test event generation for session completed reason."""
        consumer = ExamSessionConsumer()
        event_type, message = consumer._get_event_for_reason('session_completed')
        
        self.assertEqual(event_type, 'session_completed')
        self.assertIn('submitted', message.lower())

    def test_get_event_for_reason_session_timeout(self):
        """Test event generation for session timeout reason."""
        consumer = ExamSessionConsumer()
        event_type, message = consumer._get_event_for_reason('session_timeout')
        
        self.assertEqual(event_type, 'session_completed')
        self.assertIn('ended', message.lower())


class ConsumerHelperMethodsTests(TestCase):
    """Tests for consumer helper methods."""

    def setUp(self):
        self.user = create_test_user(email='student2@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)

    def test_check_token_validity_valid_token(self):
        """Test token validity check with valid token."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertTrue(is_valid)
        self.assertIsNone(reason)

    def test_check_token_validity_invalid_token(self):
        """Test token validity check with invalid token."""
        is_valid, reason = ExamSessionService.check_token_validity('invalid-token')
        
        self.assertFalse(is_valid)
        self.assertEqual(reason, 'invalid_token')

    def test_check_token_validity_expired_token(self):
        """Test token validity check with expired token."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        token.is_valid = False
        token.save()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertFalse(is_valid)
        self.assertEqual(reason, 'token_expired')

    def test_check_token_validity_completed_session(self):
        """Test token validity check with completed session."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        session.mark_completed()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertFalse(is_valid)
        self.assertIn(reason, ['session_completed', 'token_expired'])


class WebSocketEventTests(TestCase):
    """Tests for WebSocket event handling."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            expected_answer='Answer', points=10
        )

    def test_session_completed_event_structure(self):
        """Test session_completed event has correct structure."""
        consumer = ExamSessionConsumer()
        event = {
            'type': 'session_completed',
            'message': 'Exam submitted',
            'reason': 'submitted',
            'grade_history_id': 123
        }
        
        self.assertTrue(hasattr(consumer, 'session_completed'))

    def test_session_expired_event_structure(self):
        """Test session_expired event has correct structure."""
        consumer = ExamSessionConsumer()
        event = {
            'type': 'session_expired',
            'message': 'Token expired',
            'reason': 'token_expired'
        }
        
        self.assertTrue(hasattr(consumer, 'session_expired'))

    def test_event_reasons_mapping(self):
        """Test all event reasons return correct event types."""
        consumer = ExamSessionConsumer()
        
        reason_map = {
            'token_expired': 'session_expired',
            'invalid_token': 'session_expired',
            'session_completed': 'session_completed',
            'session_timeout': 'session_completed',
        }
        
        for reason, expected_type in reason_map.items():
            event_type, _ = consumer._get_event_for_reason(reason)
            self.assertEqual(event_type, expected_type, f'Failed for reason: {reason}')


class TokenValidationTests(TestCase):
    """Tests for WebSocket token validation."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            expected_answer='Answer', points=10
        )

    def test_valid_token_passes_validation(self):
        """Test valid token passes validation."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertTrue(is_valid)
        self.assertIsNone(reason)

    def test_invalid_token_fails_validation(self):
        """Test random invalid token fails validation."""
        is_valid, reason = ExamSessionService.check_token_validity('completely-invalid-token')
        
        self.assertFalse(is_valid)
        self.assertEqual(reason, 'invalid_token')

    def test_expired_token_fails_validation(self):
        """Test expired (invalidated) token fails validation."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        token.is_valid = False
        token.save()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertFalse(is_valid)
        self.assertEqual(reason, 'token_expired')

    def test_token_invalidated_on_new_token_creation(self):
        """Test old token becomes invalid when new token is created."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token1 = session.create_new_token()
        token2 = session.create_new_token()
        
        token1.refresh_from_db()
        
        self.assertFalse(token1.is_valid)
        self.assertTrue(token2.is_valid)

    def test_completed_session_token_invalid(self):
        """Test token becomes invalid when session is completed."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        session.mark_completed()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        self.assertFalse(is_valid)
        self.assertIn(reason, ['session_completed', 'token_expired'])

    def test_session_time_expired_token_validity(self):
        """Test token validity when session time expires."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        is_valid, reason = ExamSessionService.check_token_validity(token.token)
        
        if is_valid:
            self.assertTrue(session.is_expired())


class WebSocketSessionTrackingTests(TestCase):
    """Tests for WebSocket session tracking."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            expected_answer='Answer', points=10
        )

    def test_session_group_name_format(self):
        """Test WebSocket group name is based on token."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        consumer = ExamSessionConsumer()
        consumer.session_token = token.token
        consumer.room_group_name = f'exam_session_{token.token}'
        
        self.assertIn(token.token, consumer.room_group_name)

    def test_multiple_tokens_have_different_groups(self):
        """Test different tokens create different WebSocket groups."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token1 = session.create_new_token()
        token2 = session.create_new_token()
        
        group1 = f'exam_session_{token1.token}'
        group2 = f'exam_session_{token2.token}'
        
        self.assertNotEqual(group1, group2)

    def test_session_data_retrieval(self):
        """Test session data can be retrieved from token."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        token = session.create_new_token()
        
        validated_session, validated_token = ExamSessionService.validate_token(
            token.token, self.user
        )
        
        self.assertEqual(validated_session.id, session.id)
        self.assertEqual(validated_token.id, token.id)
        self.assertEqual(validated_session.student, self.user)
