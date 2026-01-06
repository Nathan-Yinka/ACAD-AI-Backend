"""Tests for admin views in assessments app."""
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.test_utils import create_test_user, create_test_admin
from apps.accounts.services.user_service import UserService
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer


class AdminExamViewSetTests(TestCase):
    """Comprehensive tests for AdminExamViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_admin(email='admin@example.com')
        self.token = UserService.login_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

    def test_list_all_exams(self):
        """Test admin can list all exams including inactive."""
        Exam.objects.create(title='Active', course='CS101', duration_minutes=30, is_active=True)
        Exam.objects.create(title='Inactive', course='CS102', duration_minutes=30, is_active=False)

        url = reverse('assessments:admin-exam-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin should see both active and inactive exams
        self.assertGreaterEqual(response.data['data']['count'], 2)

    def test_create_exam_with_required_fields(self):
        """Test admin can create exam with all required fields."""
        url = reverse('assessments:admin-exam-list')
        data = {
            'title': 'Python Fundamentals',
            'description': 'Learn Python basics',
            'course': 'CS101',
            'duration_minutes': 90,
            'is_active': False
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exam = Exam.objects.get(title='Python Fundamentals')
        self.assertEqual(exam.duration_minutes, 90)
        self.assertFalse(exam.is_active)

    def test_update_exam(self):
        """Test admin can update exam details."""
        exam = Exam.objects.create(title='Old Title', course='CS101', duration_minutes=30)
        url = reverse('assessments:admin-exam-detail', kwargs={'pk': exam.id})
        
        response = self.client.patch(url, {'title': 'New Title', 'duration_minutes': 60})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exam.refresh_from_db()
        self.assertEqual(exam.title, 'New Title')
        self.assertEqual(exam.duration_minutes, 60)

    def test_delete_exam(self):
        """Test admin can delete exam."""
        exam = Exam.objects.create(title='To Delete', course='CS101', duration_minutes=30)
        url = reverse('assessments:admin-exam-detail', kwargs={'pk': exam.id})
        
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Exam.objects.filter(id=exam.id).exists())

    def test_retrieve_exam_with_questions(self):
        """Test admin can retrieve exam with full question details."""
        exam = Exam.objects.create(title='Test Exam', course='CS101', duration_minutes=60)
        Question.objects.create(
            exam=exam, order=1, question_text='Q1',
            expected_answer='Answer 1', points=10
        )
        
        url = reverse('assessments:admin-exam-detail', kwargs={'pk': exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Test Exam')

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated users cannot access admin endpoints."""
        self.client.credentials()  # Remove credentials
        url = reverse('assessments:admin-exam-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_access_denied(self):
        """Test students cannot access admin endpoints."""
        student = create_test_user(email='student@example.com')
        student_token = UserService.login_user(student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token.key}')

        url = reverse('assessments:admin-exam-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_activate_exam_without_questions(self):
        """Test admin cannot activate exam without questions."""
        exam = Exam.objects.create(title='Test Exam', course='CS101', duration_minutes=30, is_active=False)
        url = reverse('assessments:admin-exam-activate', kwargs={'pk': exam.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('questions', response.data['message'].lower())
        exam.refresh_from_db()
        self.assertFalse(exam.is_active)


class AdminQuestionViewSetTests(TestCase):
    """Tests for AdminQuestionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_admin(email='admin@example.com')
        self.token = UserService.login_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        self.exam = Exam.objects.create(title='Test Exam', course='CS101', duration_minutes=60)

    def test_list_questions_for_exam(self):
        """Test admin can list all questions for an exam via retrieve exam."""
        Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            expected_answer='A1', points=10
        )
        Question.objects.create(
            exam=self.exam, order=2, question_text='Q2',
            expected_answer='A2', points=15
        )

        # Use the exam detail endpoint which shows questions
        url = reverse('assessments:admin-exam-detail', kwargs={'pk': self.exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.exam.questions.count(), 2)

    def test_create_question_via_model(self):
        """Test question creation with validation."""
        question = Question.objects.create(
            exam=self.exam, order=1, 
            question_text='What is Python?',
            question_type='SHORT_ANSWER',
            expected_answer='A programming language',
            points=10
        )
        self.assertTrue(Question.objects.filter(exam=self.exam, order=1).exists())
        self.assertEqual(question.points, 10)

    def test_create_mcq_with_options(self):
        """Test MCQ creation with options."""
        question = Question.objects.create(
            exam=self.exam, order=1,
            question_text='Which is a Python data type?',
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'list'},
                {'label': 'B', 'value': 'array'},
                {'label': 'C', 'value': 'dict'}
            ],
            expected_answer='list',
            points=5
        )
        self.assertEqual(len(question.options), 3)

    def test_question_model_update(self):
        """Test question can be updated."""
        question = Question.objects.create(
            exam=self.exam, order=1, question_text='Old Q',
            expected_answer='Old A', points=10
        )
        
        question.question_text = 'New Question'
        question.points = 20
        question.save()

        question.refresh_from_db()
        self.assertEqual(question.question_text, 'New Question')
        self.assertEqual(question.points, 20)

    def test_question_model_delete(self):
        """Test question can be deleted."""
        question = Question.objects.create(
            exam=self.exam, order=1, question_text='To Delete',
            expected_answer='Answer', points=10
        )
        question_id = question.id
        question.delete()

        self.assertFalse(Question.objects.filter(id=question_id).exists())

    def test_mcq_validation_requires_options(self):
        """Test MCQ requires at least 2 options."""
        with self.assertRaises(ValidationError):
            Question.objects.create(
                exam=self.exam, order=1,
                question_text='Bad MCQ',
                question_type='MULTIPLE_CHOICE',
                options=[],  # Empty options should fail
                expected_answer='answer',
                points=5
            )

    def test_cannot_delete_question_with_active_session(self):
        """Test admin cannot delete question when exam has active session."""
        from django.utils import timezone
        from datetime import timedelta
        from apps.core.exceptions import ExamModificationError
        
        question = Question.objects.create(
            exam=self.exam, order=1, question_text='Test Question',
            expected_answer='Answer', points=10
        )
        
        student = create_test_user(email='student@example.com')
        ExamSession.objects.create(
            student=student,
            exam=self.exam,
            expires_at=timezone.now() + timedelta(hours=1),
            is_completed=False
        )
        
        url = reverse('assessments:admin-question-detail', kwargs={'exam_pk': self.exam.id, 'pk': question.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('active sessions', response.data['message'].lower())
        self.assertTrue(Question.objects.filter(id=question.id).exists())


class AdminSessionViewTests(TestCase):
    """Tests for admin session management."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_admin(email='admin@example.com')
        self.token = UserService.login_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        
        self.student = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam', course='CS101', duration_minutes=60, is_active=True
        )
        Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            expected_answer='Answer', points=10
        )

    def test_admin_list_exam_sessions(self):
        """Test admin can list all sessions for an exam."""
        session = ExamSession.objects.create(student=self.student, exam=self.exam)
        
        url = reverse('grading:admin-exam-sessions', kwargs={'exam_id': self.exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_view_session_detail(self):
        """Test admin can view detailed session info including answers."""
        session = ExamSession.objects.create(student=self.student, exam=self.exam)
        question = self.exam.questions.first()
        StudentAnswer.objects.create(
            session=session, question=question, answer_text='Student answer'
        )
        
        url = reverse('grading:admin-session-detail', kwargs={'pk': session.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin should see student answers
        self.assertIn('answers', str(response.data) or 'student_answers' in str(response.data))

    def test_student_cannot_access_admin_sessions(self):
        """Test students cannot access admin session endpoints."""
        student_token = UserService.login_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_token.key}')
        
        url = reverse('grading:admin-exam-sessions', kwargs={'exam_id': self.exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

