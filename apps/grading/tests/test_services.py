"""Tests for grading services."""
from django.test import TestCase
from unittest.mock import patch
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer
from apps.grading.services import GradingService
from apps.grading.services.graders import get_grading_service
from apps.grading.services.graders.mock_grading import MockGradingService
from apps.grading.models import GradeHistory


class MockGradingServiceTests(TestCase):
    """Tests for MockGradingService."""

    def setUp(self):
        self.grading_service = MockGradingService()

    def test_grade_exact_match(self):
        """Test exact match grading."""
        result = self.grading_service.grade_answer(
            answer_text='Python',
            expected_answer='Python',
            max_points=10
        )
        self.assertEqual(result['score'], 10.0)

    def test_grade_similar_answer(self):
        """Test similar answer grading."""
        result = self.grading_service.grade_answer(
            answer_text='python programming language',
            expected_answer='python programming language',
            max_points=10
        )
        self.assertEqual(result['score'], 10.0)

    def test_grade_wrong_answer(self):
        """Test completely wrong answer gets zero."""
        result = self.grading_service.grade_answer(
            answer_text='xyz abc 123',
            expected_answer='python programming language',
            max_points=10
        )
        self.assertEqual(result['score'], 0.0)

    def test_grade_partial_keyword_match(self):
        """Test partial keyword matching for essay."""
        result = self.grading_service.grade_answer(
            answer_text='Python is a programming language used for development',
            expected_answer='programming language used for software development',
            max_points=10
        )
        # Should get partial credit for matching keywords
        self.assertGreater(result['score'], 0)
        self.assertLessEqual(result['score'], 10.0)

    def test_grade_empty_answer(self):
        """Test empty answer gets zero."""
        result = self.grading_service.grade_answer(
            answer_text='',
            expected_answer='Python',
            max_points=10
        )
        self.assertEqual(result['score'], 0.0)


class GradingServiceTests(TestCase):
    """Tests for GradingService."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        self.q1 = Question.objects.create(
            exam=self.exam, order=1,
            question_text='What is Python?',
            question_type='SHORT_ANSWER',
            expected_answer='A programming language',
            points=10
        )
        self.q2 = Question.objects.create(
            exam=self.exam, order=2,
            question_text='Select correct option',
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            expected_answer='opt1',
            points=5
        )
        self.session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=self.session,
            question=self.q1,
            answer_text='Python is a programming language'
        )
        StudentAnswer.objects.create(
            session=self.session,
            question=self.q2,
            answer_text='opt1'
        )

    def test_grade_session(self):
        """Test grading a complete session."""
        grade_history = GradingService.grade_session(self.session, grading_method='manual')

        self.assertEqual(grade_history.status, 'COMPLETED')
        self.assertIsNotNone(grade_history.total_score)
        self.assertEqual(grade_history.max_score, 15)  # 10 + 5

    def test_grade_session_creates_history(self):
        """Test grading creates grade history entry."""
        grade_history = GradingService.grade_session(self.session)

        self.assertTrue(GradeHistory.objects.filter(id=grade_history.id).exists())
        self.assertEqual(grade_history.student, self.user)
        self.assertEqual(grade_history.exam, self.exam)

    def test_grade_session_marks_completed(self):
        """Test grading marks session as completed."""
        GradingService.grade_session(self.session)

        self.session.refresh_from_db()
        self.assertTrue(self.session.is_completed)

    def test_grade_already_completed_session(self):
        """Test grading already completed session returns existing grade."""
        grade1 = GradingService.grade_session(self.session)
        grade2 = GradingService.grade_session(self.session)

        self.assertEqual(grade1.id, grade2.id)


class GetGradingServiceTests(TestCase):
    """Tests for get_grading_service factory."""

    @patch('apps.grading.services.graders.settings')
    def test_returns_mock_service_by_default(self, mock_settings):
        """Test returns mock service when configured."""
        mock_settings.GRADING_SERVICE = 'mock'
        service = get_grading_service()
        self.assertIsInstance(service, MockGradingService)

    @patch('apps.grading.services.graders.settings')
    def test_returns_mock_for_unknown_config(self, mock_settings):
        """Test returns mock service for unknown config."""
        mock_settings.GRADING_SERVICE = 'unknown'
        service = get_grading_service()
        self.assertIsInstance(service, MockGradingService)
