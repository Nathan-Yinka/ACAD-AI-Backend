"""Integration tests for background grading tasks."""
import json
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer
from apps.grading.tasks import schedule_session_expiry, check_expired_sessions, grade_expired_session
from apps.grading.models import GradeHistory
from apps.assessments.models import Submission


class BackgroundGradingIntegrationTests(TestCase):
    """Integration tests for background grading tasks."""
    
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
    
    def test_schedule_session_expiry_grades_in_background(self):
        """Test that scheduled task grades session in background."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=self.q1,
            answer_text='A programming language'
        )
        StudentAnswer.objects.create(
            session=session,
            question=self.q2,
            answer_text='opt1'
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            schedule_session_expiry(session.id)
        
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        grade_history = GradeHistory.objects.get(session_id=session.id)
        self.assertEqual(grade_history.status, 'COMPLETED')
        self.assertIsNotNone(grade_history.total_score)
        self.assertEqual(grade_history.max_score, 15)
        self.assertEqual(grade_history.grading_method, 'timeout')
        
        submission = Submission.objects.get(exam=self.exam, student=self.user)
        self.assertEqual(submission.status, 'GRADED')
        self.assertIsNotNone(submission.total_score)
    
    def test_background_grading_with_mcq_single(self):
        """Test background grading handles MCQ single choice correctly."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=self.q2,
            answer_text='opt1'
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            schedule_session_expiry(session.id)
        
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        grade_history = GradeHistory.objects.get(session_id=session.id)
        submission = Submission.objects.get(exam=self.exam, student=self.user)
        
        answer = submission.answers.get(question=self.q2)
        self.assertEqual(answer.answer_text, 'opt1')
        self.assertIsNotNone(answer.score)
        self.assertGreaterEqual(answer.score, 0)
        self.assertLessEqual(answer.score, 5)
    
    def test_background_grading_with_mcq_multiple(self):
        """Test background grading handles MCQ multiple choice correctly."""
        q3 = Question.objects.create(
            exam=self.exam, order=3,
            question_text='Select all correct',
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True,
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'}
            ],
            expected_answer='["opt1", "opt2"]',
            points=10
        )
        
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=q3,
            answer_text=json.dumps(['opt1', 'opt2'])
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            schedule_session_expiry(session.id)
        
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        submission = Submission.objects.get(exam=self.exam, student=self.user)
        answer = submission.answers.get(question=q3)
        self.assertIn(answer.answer_text, [json.dumps(['opt1', 'opt2']), '["opt1", "opt2"]'])
        self.assertIsNotNone(answer.score)
        self.assertGreaterEqual(answer.score, 0)
        self.assertLessEqual(answer.score, 10)
    
    def test_background_grading_with_short_answer(self):
        """Test background grading handles short answer correctly."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=self.q1,
            answer_text='Python is a programming language'
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            schedule_session_expiry(session.id)
        
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        submission = Submission.objects.get(exam=self.exam, student=self.user)
        answer = submission.answers.get(question=self.q1)
        self.assertEqual(answer.answer_text, 'Python is a programming language')
        self.assertIsNotNone(answer.score)
        self.assertGreaterEqual(answer.score, 0)
        self.assertLessEqual(answer.score, 10)
    
    def test_check_expired_sessions_finds_and_grades(self):
        """Test periodic task finds and grades expired sessions."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=5)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=self.q1,
            answer_text='Test answer'
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            count = check_expired_sessions()
        
        self.assertEqual(count, 1)
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        grade_history = GradeHistory.objects.filter(session_id=session.id).first()
        self.assertIsNotNone(grade_history)
        self.assertEqual(grade_history.status, 'COMPLETED')
    
    def test_grade_expired_session_by_id(self):
        """Test grading expired session by ID works."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        StudentAnswer.objects.create(
            session=session,
            question=self.q1,
            answer_text='Test answer'
        )
        
        with patch('apps.grading.tasks.session_tasks.get_channel_layer') as mock_channel:
            mock_channel.return_value = None
            result = grade_expired_session(session.id)
        
        self.assertIsNotNone(result)
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        
        grade_history = GradeHistory.objects.get(session_id=session.id)
        self.assertEqual(grade_history.status, 'COMPLETED')

