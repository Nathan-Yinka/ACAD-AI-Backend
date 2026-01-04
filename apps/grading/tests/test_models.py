"""Tests for grading models."""
from django.test import TestCase
from django.utils import timezone
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam
from apps.grading.models import GradeHistory


class GradeHistoryModelTests(TestCase):
    """Tests for the GradeHistory model."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60
        )

    def test_grade_history_creation(self):
        """Test grade history creation."""
        grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=1,
            status='COMPLETED',
            total_score=85.0,
            max_score=100.0,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )

        self.assertEqual(grade.status, 'COMPLETED')
        self.assertEqual(grade.total_score, 85.0)

    def test_calculate_percentage(self):
        """Test percentage calculation."""
        grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=1,
            total_score=85.0,
            max_score=100.0,
            started_at=timezone.now()
        )

        self.assertEqual(grade.calculate_percentage(), 85.0)

    def test_calculate_percentage_zero_max(self):
        """Test percentage with zero max score."""
        grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=1,
            total_score=0,
            max_score=0,
            started_at=timezone.now()
        )

        self.assertEqual(grade.calculate_percentage(), 0.0)

    def test_grade_history_str(self):
        """Test string representation."""
        grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=1,
            status='COMPLETED',
            started_at=timezone.now()
        )

        expected = f'{self.user.email} - {self.exam.title} - COMPLETED'
        self.assertEqual(str(grade), expected)
