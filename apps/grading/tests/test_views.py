"""Tests for grading views."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.test_utils import create_test_user, create_test_admin
from apps.accounts.services.user_service import UserService
from apps.assessments.models import Exam
from apps.grading.models import GradeHistory


class GradeHistoryViewTests(TestCase):
    """Tests for student grade history views."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(email='student@example.com')
        self.token = UserService.login_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60
        )
        self.grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=1,
            status='COMPLETED',
            total_score=85.0,
            max_score=100.0,
            percentage=85.0,
            answers_data=[
                {'question_order': 1, 'score': 8.5, 'max_score': 10},
                {'question_order': 2, 'score': 5.0, 'max_score': 5},
            ],
            started_at=timezone.now(),
            submitted_at=timezone.now(),
            graded_at=timezone.now()
        )

    def test_list_grade_history(self):
        """Test listing grade history."""
        url = reverse('grading:history-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_list_only_own_grades(self):
        """Test user only sees their own grades, not others'."""
        other_user = create_test_user(email='other@example.com')
        GradeHistory.objects.create(
            student=other_user,
            exam=self.exam,
            session_id=999,  # Distinct session ID
            started_at=timezone.now()
        )

        url = reverse('grading:history-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Parse response to get grade count
        data = response.data.get('data', {})
        if isinstance(data, dict) and 'data' in data:
            data = data['data']  # Handle nested data
        
        count = data.get('count', 0)
        # Should only see 1 grade (own), not 2 (own + other)
        self.assertEqual(count, 1)

    def test_get_grade_detail(self):
        """Test retrieving grade detail."""
        url = reverse('grading:history-detail', kwargs={'pk': self.grade.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['data']['total_score']), 85.0)
        # Should have question_scores, not full answers_data
        self.assertIn('question_scores', response.data['data'])

    def test_grade_detail_shows_scores_only(self):
        """Test student grade detail only shows scores, not answers."""
        url = reverse('grading:history-detail', kwargs={'pk': self.grade.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertIn('question_scores', response.data['data'])
        question_scores = response.data['data']['question_scores']
        self.assertEqual(len(question_scores), 2)
        # Should only have order, score, max_score
        self.assertIn('question_order', question_scores[0])
        self.assertIn('score', question_scores[0])
        self.assertIn('max_score', question_scores[0])
        # Should NOT have answer details
        self.assertNotIn('answer_text', question_scores[0])
        self.assertNotIn('expected_answer', question_scores[0])

    def test_cannot_access_others_grade(self):
        """Test cannot access another user's grade."""
        other_user = create_test_user(email='other2@example.com')
        other_grade = GradeHistory.objects.create(
            student=other_user,
            exam=self.exam,
            session_id=2,
            started_at=timezone.now()
        )

        url = reverse('grading:history-detail', kwargs={'pk': other_grade.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminGradeViewTests(TestCase):
    """Tests for admin grade views."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_admin(email='admin@example.com')
        self.token = UserService.login_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.key}')

        self.student = create_test_user(email='student2@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60
        )
        self.grade = GradeHistory.objects.create(
            student=self.student,
            exam=self.exam,
            session_id=1,
            status='COMPLETED',
            total_score=85.0,
            max_score=100.0,
            answers_data=[
                {
                    'question_order': 1,
                    'question_text': 'What is Python?',
                    'expected_answer': 'A programming language',
                    'student_answer': 'Python is a language',
                    'score': 8.5,
                    'max_score': 10
                }
            ],
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )

    def test_admin_list_all_grades(self):
        """Test admin can list all grades."""
        url = reverse('grading:admin-grades-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_grade_detail_shows_full_data(self):
        """Test admin can see full question and answer data."""
        url = reverse('grading:admin-grade-detail', kwargs={'pk': self.grade.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have full answers_data with question details
        self.assertIn('answers_data', response.data['data'])
        answer_data = response.data['data']['answers_data'][0]
        self.assertIn('question_text', answer_data)
        self.assertIn('expected_answer', answer_data)
        self.assertIn('student_answer', answer_data)

    def test_admin_list_exam_grades(self):
        """Test admin can list grades for specific exam."""
        url = reverse('grading:admin-exam-grades', kwargs={'exam_id': self.exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_access_admin_endpoints(self):
        """Test non-admin cannot access admin endpoints."""
        user_token = UserService.login_user(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token.key}')

        url = reverse('grading:admin-grades-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
