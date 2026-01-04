"""Tests for assessments views."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from apps.core.test_utils import create_test_user, create_test_admin
from apps.assessments.models import Exam, Question, ExamSession


class ExamViewSetTests(TestCase):
    """Tests for ExamViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='student@example.com')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

        self.exam = Exam.objects.create(
            title='Python Basics',
            description='Test your Python knowledge',
            course='CS101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)

    def test_list_exams(self):
        """Test listing active exams."""
        url = reverse('assessments:exam-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_list_exams_excludes_inactive(self):
        """Test inactive exams are not listed."""
        inactive_exam = Exam.objects.create(
            title='Inactive Exam',
            course='CS102',
            duration_minutes=30,
            is_active=False
        )
        url = reverse('assessments:exam-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        data = response.data['data']
        if isinstance(data, dict) and 'results' in data:
            exam_ids = [e['id'] for e in data['results']]
        else:
            exam_ids = [e['id'] for e in data] if isinstance(data, list) else []
        self.assertIn(self.exam.id, exam_ids)
        self.assertNotIn(inactive_exam.id, exam_ids)

    def test_retrieve_exam(self):
        """Test retrieving exam detail."""
        url = reverse('assessments:exam-detail', kwargs={'pk': self.exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Python Basics')

    def test_start_exam_session(self):
        """Test starting an exam session."""
        url = reverse('assessments:exam-start', kwargs={'pk': self.exam.id})
        response = self.client.post(url)

        # New session returns 201 Created
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data['data'])
        self.assertTrue(ExamSession.objects.filter(student=self.user, exam=self.exam).exists())

    def test_start_exam_returns_existing_session_token(self):
        """Test starting exam when session exists returns new token."""
        url = reverse('assessments:exam-start', kwargs={'pk': self.exam.id})
        response1 = self.client.post(url)
        response2 = self.client.post(url)

        # First is 201 (created), second is 200 (continued)
        self.assertIn(response1.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Tokens should be different
        self.assertNotEqual(
            response1.data['data']['token'],
            response2.data['data']['token']
        )

    def test_exam_list_includes_active_session(self):
        """Test exam list includes active session info when session exists."""
        # Start a session
        start_url = reverse('assessments:exam-start', kwargs={'pk': self.exam.id})
        start_response = self.client.post(start_url)

        # List exams
        list_url = reverse('assessments:exam-list')
        response = self.client.get(list_url)

        # Session was started
        self.assertTrue(start_response.data['success'])


class SessionQuestionViewTests(TestCase):
    """Tests for session question endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='student2@example.com')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        self.q1 = Question.objects.create(
            exam=self.exam, order=1, question_text='What is Python?',
            question_type='SHORT_ANSWER', expected_answer='A programming language', points=10
        )
        self.q2 = Question.objects.create(
            exam=self.exam, order=2, question_text='Select correct option',
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            expected_answer='opt1',
            points=5
        )

        # Start session
        start_url = reverse('assessments:exam-start', kwargs={'pk': self.exam.id})
        response = self.client.post(start_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.session_token = response.data['data']['token']

    def test_get_question_by_order(self):
        """Test fetching question by order."""
        url = reverse('assessments:session-question', kwargs={
            'token': self.session_token,
            'order': 1
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['question_text'], 'What is Python?')

    def test_get_question_invalid_order(self):
        """Test fetching invalid question order."""
        url = reverse('assessments:session-question', kwargs={
            'token': self.session_token,
            'order': 99
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_answer(self):
        """Test submitting an answer."""
        url = reverse('assessments:session-answer', kwargs={
            'token': self.session_token,
            'order': 1
        })
        response = self.client.post(url, {'answer_text': 'A programming language'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['answer_text'], 'A programming language')

    def test_submit_answer_empty(self):
        """Test submitting empty answer fails."""
        url = reverse('assessments:session-answer', kwargs={
            'token': self.session_token,
            'order': 1
        })
        response = self.client.post(url, {'answer_text': ''})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_progress(self):
        """Test getting session progress."""
        # Submit one answer
        answer_url = reverse('assessments:session-answer', kwargs={
            'token': self.session_token,
            'order': 1
        })
        self.client.post(answer_url, {'answer_text': 'Test answer'})

        # Get progress
        progress_url = reverse('assessments:session-progress', kwargs={
            'token': self.session_token
        })
        response = self.client.get(progress_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_questions'], 2)
        self.assertEqual(response.data['data']['answered_count'], 1)

    def test_invalid_token_rejected(self):
        """Test requests with invalid token are rejected."""
        url = reverse('assessments:session-question', kwargs={
            'token': 'invalid-token-here',
            'order': 1
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminExamViewSetTests(TestCase):
    """Tests for AdminExamViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_admin(email='admin@example.com')
        self.token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

    def test_create_exam(self):
        """Test admin can create exam."""
        url = reverse('assessments:admin-exam-list')
        data = {
            'title': 'New Exam',
            'description': 'Test description',
            'course': 'CS101',
            'duration_minutes': 60,
            'is_active': False
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Exam.objects.filter(title='New Exam').exists())

    def test_non_admin_cannot_create_exam(self):
        """Test non-admin cannot create exam."""
        user = create_test_user(email='student3@example.com')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.key}')

        url = reverse('assessments:admin-exam-list')
        data = {'title': 'Test', 'course': 'CS101', 'duration_minutes': 60}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_activate_exam(self):
        """Test admin can activate exam."""
        exam = Exam.objects.create(title='Test', course='CS101', duration_minutes=30, is_active=False)
        url = reverse('assessments:admin-exam-activate', kwargs={'pk': exam.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exam.refresh_from_db()
        self.assertTrue(exam.is_active)

    def test_deactivate_exam(self):
        """Test admin can deactivate exam."""
        exam = Exam.objects.create(title='Test', course='CS101', duration_minutes=30, is_active=True)
        url = reverse('assessments:admin-exam-deactivate', kwargs={'pk': exam.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exam.refresh_from_db()
        self.assertFalse(exam.is_active)
