"""Tests for assessments models."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.core.test_utils import create_test_user
from apps.assessments.models import (
    Exam, Question, Submission, Answer, ExamSession, StudentAnswer, SessionToken
)


class ExamModelTests(TestCase):
    """Tests for the Exam model."""

    def setUp(self):
        self.exam = Exam.objects.create(
            title='Python Basics',
            description='Test your Python knowledge',
            course='CS101',
            duration_minutes=60,
            is_active=True
        )

    def test_exam_creation(self):
        """Test exam is created correctly."""
        self.assertEqual(self.exam.title, 'Python Basics')
        self.assertEqual(self.exam.duration_minutes, 60)
        self.assertTrue(self.exam.is_active)

    def test_exam_str_representation(self):
        """Test exam string representation."""
        self.assertEqual(str(self.exam), 'Python Basics')

    def test_get_questions_count(self):
        """Test questions count method."""
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='A1', points=10)
        Question.objects.create(exam=self.exam, order=2, question_text='Q2', expected_answer='A2', points=10)

        self.assertEqual(self.exam.get_questions_count(), 2)

    def test_get_max_score(self):
        """Test max score calculation."""
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='A1', points=10)
        Question.objects.create(exam=self.exam, order=2, question_text='Q2', expected_answer='A2', points=15)

        self.assertEqual(self.exam.get_max_score(), 25)


class QuestionModelTests(TestCase):
    """Tests for the Question model."""

    def setUp(self):
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=30
        )
        self.question = Question.objects.create(
            exam=self.exam,
            order=1,
            question_text='What is Python?',
            question_type='SHORT_ANSWER',
            expected_answer='A programming language',
            points=10
        )

    def test_question_creation(self):
        """Test question is created correctly."""
        self.assertEqual(self.question.question_text, 'What is Python?')
        self.assertEqual(self.question.points, 10)

    def test_question_str_representation(self):
        """Test question string representation."""
        expected = f'{self.exam.title} - Question 1'
        self.assertEqual(str(self.question), expected)

    def test_multiple_choice_question(self):
        """Test MCQ with options."""
        mcq = Question.objects.create(
            exam=self.exam,
            order=2,
            question_text='Which is a data type?',
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'list'},
                {'label': 'B', 'value': 'array'},
                {'label': 'C', 'value': 'dict'}
            ],
            expected_answer='list',
            points=5
        )

        self.assertEqual(len(mcq.options), 3)
        self.assertEqual(mcq.options[0]['value'], 'list')


class ExamSessionModelTests(TestCase):
    """Tests for the ExamSession model."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60
        )
        self.session = ExamSession.objects.create(
            student=self.user,
            exam=self.exam
        )

    def test_session_creation(self):
        """Test session is created with correct expiry."""
        self.assertIsNotNone(self.session.started_at)
        self.assertIsNotNone(self.session.expires_at)
        self.assertFalse(self.session.is_completed)

    def test_session_expiry_time(self):
        """Test session expiry is correctly calculated."""
        # Check expiry is roughly 60 minutes after start (within a second)
        expected_duration = timedelta(minutes=60)
        actual_duration = self.session.expires_at - self.session.started_at
        self.assertAlmostEqual(
            actual_duration.total_seconds(),
            expected_duration.total_seconds(),
            delta=1  # Allow 1 second difference
        )

    def test_is_expired(self):
        """Test is_expired method."""
        self.assertFalse(self.session.is_expired())

        # Force expire
        self.session.expires_at = timezone.now() - timedelta(minutes=1)
        self.session.save()
        self.assertTrue(self.session.is_expired())

    def test_is_active(self):
        """Test is_active method."""
        self.assertTrue(self.session.is_active())

        # Mark completed
        self.session.mark_completed()
        self.assertFalse(self.session.is_active())

    def test_time_remaining_seconds(self):
        """Test time_remaining_seconds method."""
        remaining = self.session.time_remaining_seconds()
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, 3600)

    def test_create_new_token(self):
        """Test token creation."""
        token = self.session.create_new_token()
        self.assertIsNotNone(token)
        self.assertTrue(token.is_valid)

    def test_token_invalidation(self):
        """Test old tokens are invalidated when new one is created."""
        token1 = self.session.create_new_token()
        token2 = self.session.create_new_token()

        token1.refresh_from_db()
        self.assertFalse(token1.is_valid)
        self.assertTrue(token2.is_valid)


class StudentAnswerModelTests(TestCase):
    """Tests for the StudentAnswer model."""

    def setUp(self):
        self.user = create_test_user(email='student2@example.com')
        self.exam = Exam.objects.create(title='Test', course='T101', duration_minutes=30)
        self.question = Question.objects.create(
            exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10
        )
        self.session = ExamSession.objects.create(student=self.user, exam=self.exam)

    def test_student_answer_creation(self):
        """Test student answer creation."""
        answer = StudentAnswer.objects.create(
            session=self.session,
            question=self.question,
            answer_text='My answer'
        )
        self.assertEqual(answer.answer_text, 'My answer')
        self.assertIsNotNone(answer.answered_at)

    def test_unique_answer_per_question(self):
        """Test only one answer per question per session."""
        StudentAnswer.objects.create(
            session=self.session,
            question=self.question,
            answer_text='First answer'
        )
        # Update instead of create duplicate
        answer, created = StudentAnswer.objects.update_or_create(
            session=self.session,
            question=self.question,
            defaults={'answer_text': 'Updated answer'}
        )
        self.assertFalse(created)
        self.assertEqual(answer.answer_text, 'Updated answer')
