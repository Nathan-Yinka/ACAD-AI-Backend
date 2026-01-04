"""Tests for grading tasks."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer
from apps.grading.tasks import check_expired_sessions, schedule_session_expiry, grade_expired_session
from apps.grading.models import GradeHistory


class SessionTasksTests(TestCase):
    """Tests for session-related Celery tasks."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        self.question = Question.objects.create(
            exam=self.exam, order=1,
            question_text='Q1',
            question_type='SHORT_ANSWER',
            expected_answer='Answer',
            points=10
        )

    def test_check_expired_sessions_finds_expired(self):
        """Test check_expired_sessions finds and grades expired sessions."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=5)
        session.save()

        StudentAnswer.objects.create(
            session=session,
            question=self.question,
            answer_text='Test answer'
        )

        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            count = check_expired_sessions()

        self.assertEqual(count, 1)
        session.refresh_from_db()
        self.assertTrue(session.is_completed)

    def test_check_expired_sessions_skips_completed(self):
        """Test check_expired_sessions skips already completed sessions."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=5)
        session.is_completed = True
        session.save()

        count = check_expired_sessions()

        self.assertEqual(count, 0)

    def test_schedule_session_expiry_grades_expired(self):
        """Test scheduled task grades expired session."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()

        StudentAnswer.objects.create(
            session=session,
            question=self.question,
            answer_text='Test answer'
        )

        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            schedule_session_expiry(session.id)

        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        self.assertTrue(GradeHistory.objects.filter(session_id=session.id).exists())

    def test_schedule_session_expiry_skips_if_not_expired(self):
        """Test scheduled task reschedules if not yet expired."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        # Session not expired yet

        with patch('apps.grading.tasks.session_tasks.schedule_session_expiry.apply_async') as mock_apply:
            schedule_session_expiry(session.id)
            # Should reschedule
            mock_apply.assert_called_once()

    def test_schedule_session_expiry_skips_completed(self):
        """Test scheduled task skips completed session."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.is_completed = True
        session.save()

        # Should return without error
        result = schedule_session_expiry(session.id)
        self.assertIsNone(result)

    def test_grade_expired_session_by_id(self):
        """Test grading expired session by ID."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()

        StudentAnswer.objects.create(
            session=session,
            question=self.question,
            answer_text='Test'
        )

        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            result = grade_expired_session(session.id)

        self.assertIsNotNone(result)
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
