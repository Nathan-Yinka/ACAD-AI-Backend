"""Comprehensive tests for grading services."""
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer, Submission, Answer
from apps.grading.services import GradingService
from apps.grading.services.graders.mock_grading import MockGradingService
from apps.grading.models import GradeHistory
from apps.core.exceptions import GradingError


class MockGradingServiceComprehensiveTests(TestCase):
    """Comprehensive tests for MockGradingService internal methods."""

    def setUp(self):
        self.service = MockGradingService()

    def test_normalize_text(self):
        """Test text normalization."""
        normalized = self.service._normalize_text('  Hello, World!  ')
        self.assertEqual(normalized, 'hello world')

    def test_normalize_text_removes_punctuation(self):
        """Test punctuation removal."""
        normalized = self.service._normalize_text('Python, JavaScript & Java!')
        self.assertEqual(normalized, 'python javascript java')

    def test_extract_keywords(self):
        """Test keyword extraction."""
        keywords = self.service._extract_keywords('Python is a programming language')
        self.assertIn('python', keywords)
        self.assertIn('programming', keywords)
        self.assertIn('language', keywords)
        # Stop words should be excluded
        self.assertNotIn('is', keywords)
        self.assertNotIn('a', keywords)

    def test_extract_keywords_filters_short_words(self):
        """Test short words are filtered out."""
        keywords = self.service._extract_keywords('a an the Python')
        self.assertIn('python', keywords)
        self.assertNotIn('a', keywords)

    def test_calculate_keyword_score_exact_match(self):
        """Test keyword score for exact match."""
        score = self.service._calculate_keyword_score(
            'Python programming language',
            'Python programming language'
        )
        self.assertEqual(score, 1.0)

    def test_calculate_keyword_score_partial_match(self):
        """Test keyword score for partial match."""
        score = self.service._calculate_keyword_score(
            'Python programming',
            'Python programming language development'
        )
        self.assertGreater(score, 0)
        self.assertLess(score, 1.0)

    def test_calculate_keyword_score_no_match(self):
        """Test keyword score for no match."""
        score = self.service._calculate_keyword_score(
            'Java JavaScript',
            'Python programming'
        )
        self.assertEqual(score, 0.0)

    def test_calculate_similarity_score_exact_match(self):
        """Test similarity score for exact match."""
        score = self.service._calculate_similarity_score(
            'Python is a programming language',
            'Python is a programming language'
        )
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_calculate_similarity_score_similar_text(self):
        """Test similarity score for similar text."""
        score = self.service._calculate_similarity_score(
            'Python programming language',
            'Python is a programming language'
        )
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_calculate_similarity_score_different_text(self):
        """Test similarity score for completely different text."""
        score = self.service._calculate_similarity_score(
            'Python programming',
            'Java development'
        )
        self.assertLess(score, 0.5)

    def test_calculate_similarity_score_empty_strings(self):
        """Test similarity score with empty strings."""
        score = self.service._calculate_similarity_score('', 'Python')
        self.assertEqual(score, 0.0)

    def test_generate_feedback_excellent(self):
        """Test feedback generation for excellent score."""
        feedback = self.service._generate_feedback(0.9)
        self.assertIn('Excellent', feedback)

    def test_generate_feedback_good(self):
        """Test feedback generation for good score."""
        feedback = self.service._generate_feedback(0.7)
        self.assertIn('Good', feedback)

    def test_generate_feedback_fair(self):
        """Test feedback generation for fair score."""
        feedback = self.service._generate_feedback(0.5)
        self.assertIn('Fair', feedback)

    def test_generate_feedback_weak(self):
        """Test feedback generation for weak score."""
        feedback = self.service._generate_feedback(0.3)
        self.assertIn('Weak', feedback)

    def test_generate_feedback_poor(self):
        """Test feedback generation for poor score."""
        feedback = self.service._generate_feedback(0.1)
        self.assertIn('does not meet', feedback)

    def test_grade_answer_mcq_exact_match(self):
        """Test grading MCQ with exact match."""
        result = self.service.grade_answer(
            answer_text='Python',
            expected_answer='Python',
            max_points=10
        )
        self.assertEqual(result['score'], 10.0)
        self.assertIn('feedback', result)

    def test_grade_answer_case_insensitive(self):
        """Test grading is case insensitive."""
        result1 = self.service.grade_answer('python', 'Python', 10)
        result2 = self.service.grade_answer('Python', 'python', 10)
        # Should get same or very similar scores
        self.assertAlmostEqual(result1['score'], result2['score'], places=1)

    def test_grade_answer_below_threshold(self):
        """Test answer below similarity threshold gets zero."""
        service = MockGradingService(similarity_threshold=0.8)
        result = service.grade_answer(
            answer_text='xyz',
            expected_answer='Python programming language',
            max_points=10
        )
        self.assertEqual(result['score'], 0.0)

    def test_grade_submission_with_multiple_answers(self):
        """Test grading a complete submission."""
        exam = Exam.objects.create(title='Test', course='CS101', duration_minutes=60)
        q1 = Question.objects.create(
            exam=exam, order=1, question_text='Q1',
            expected_answer='Answer 1', points=10
        )
        q2 = Question.objects.create(
            exam=exam, order=2, question_text='Q2',
            expected_answer='Answer 2', points=5
        )
        submission = Submission.objects.create(
            student=create_test_user(),
            exam=exam,
            max_score=15
        )
        Answer.objects.create(
            submission=submission,
            question=q1,
            answer_text='Answer 1'
        )
        Answer.objects.create(
            submission=submission,
            question=q2,
            answer_text='Answer 2'
        )

        result = self.service.grade_submission(submission)

        self.assertEqual(result['status'], 'GRADED')
        self.assertIn('total_score', result)
        self.assertEqual(len(result['answers']), 2)
        self.assertGreater(result['total_score'], 0)

    def test_grade_submission_empty_submission(self):
        """Test grading submission with no answers."""
        exam = Exam.objects.create(title='Test', course='CS101', duration_minutes=60)
        submission = Submission.objects.create(
            student=create_test_user(),
            exam=exam,
            max_score=0
        )

        result = self.service.grade_submission(submission)

        self.assertEqual(result['status'], 'GRADED')
        self.assertEqual(result['total_score'], 0.0)
        self.assertEqual(len(result['answers']), 0)


class GradingServiceComprehensiveTests(TestCase):
    """Comprehensive tests for GradingService."""

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

    def test_grade_session_creates_submission(self):
        """Test grading creates a Submission object."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='A programming language'
        )

        grade_history = GradingService.grade_session(session)

        self.assertTrue(Submission.objects.filter(exam=self.exam, student=self.user).exists())

    def test_grade_session_creates_answers(self):
        """Test grading creates Answer objects from StudentAnswers."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='Answer 1'
        )
        StudentAnswer.objects.create(
            session=session, question=self.q2, answer_text='opt1'
        )

        grade_history = GradingService.grade_session(session)
        submission = Submission.objects.get(exam=self.exam, student=self.user)

        self.assertEqual(submission.answers.count(), 2)

    def test_grade_session_calculates_percentage(self):
        """Test percentage is calculated correctly."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='A programming language'
        )

        grade_history = GradingService.grade_session(session)

        self.assertIsNotNone(grade_history.percentage)
        self.assertGreaterEqual(grade_history.percentage, 0)
        self.assertLessEqual(grade_history.percentage, 100)

    def test_grade_session_stores_answers_data(self):
        """Test grade history stores full answers data."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='My answer'
        )

        grade_history = GradingService.grade_session(session)

        self.assertIsNotNone(grade_history.answers_data)
        self.assertEqual(len(grade_history.answers_data), 1)
        self.assertIn('question_text', grade_history.answers_data[0])
        self.assertIn('student_answer', grade_history.answers_data[0])
        self.assertIn('expected_answer', grade_history.answers_data[0])

    def test_grade_session_updates_submission_status(self):
        """Test submission status is updated after grading."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='Answer'
        )

        GradingService.grade_session(session)
        submission = Submission.objects.get(exam=self.exam, student=self.user)

        self.assertEqual(submission.status, 'GRADED')
        self.assertIsNotNone(submission.graded_at)

    def test_grade_session_updates_answer_scores(self):
        """Test individual answer scores are updated."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='A programming language'
        )

        GradingService.grade_session(session)
        submission = Submission.objects.get(exam=self.exam, student=self.user)
        answer = submission.answers.first()

        self.assertIsNotNone(answer.score)
        self.assertIsNotNone(answer.graded_at)

    def test_grade_session_with_no_answers(self):
        """Test grading session with no student answers."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)

        grade_history = GradingService.grade_session(session)

        self.assertEqual(grade_history.total_score, 0.0)
        self.assertEqual(len(grade_history.answers_data), 0)

    def test_grade_session_with_expired_method(self):
        """Test grading with expired method."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='Answer'
        )

        grade_history = GradingService.grade_session(session, grading_method='expired')

        self.assertEqual(grade_history.grading_method, 'expired')
        self.assertEqual(grade_history.status, 'COMPLETED')

    def test_grade_session_error_handling(self):
        """Test error handling during grading."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='Answer'
        )

        with patch('apps.grading.services.grading_service.get_grading_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.grade_submission.side_effect = Exception('Grading failed')
            mock_get_service.return_value = mock_service
            
            with self.assertRaises(GradingError):
                GradingService.grade_session(session)

            # Grade history should be marked as FAILED
            grade_history = GradeHistory.objects.filter(session_id=session.id).first()
            if grade_history:
                self.assertEqual(grade_history.status, 'FAILED')

    def test_get_grade_history_all_grades(self):
        """Test getting all grade history for a student."""
        session1 = ExamSession.objects.create(student=self.user, exam=self.exam)
        GradeHistory.objects.create(
            student=self.user, exam=self.exam, session_id=session1.id,
            status='COMPLETED', started_at=timezone.now()
        )

        grades = GradingService.get_grade_history(self.user)

        self.assertGreaterEqual(len(grades), 1)

    def test_get_grade_history_for_specific_exam(self):
        """Test getting grade history for specific exam."""
        exam2 = Exam.objects.create(title='Exam 2', course='CS102', duration_minutes=30)
        
        session1 = ExamSession.objects.create(student=self.user, exam=self.exam)
        session2 = ExamSession.objects.create(student=self.user, exam=exam2)
        
        GradeHistory.objects.create(
            student=self.user, exam=self.exam, session_id=session1.id,
            status='COMPLETED', started_at=timezone.now()
        )
        GradeHistory.objects.create(
            student=self.user, exam=exam2, session_id=session2.id,
            status='COMPLETED', started_at=timezone.now()
        )

        grades = GradingService.get_grade_history(self.user, exam_id=self.exam.id)

        self.assertEqual(len(grades), 1)
        self.assertEqual(grades[0].exam.id, self.exam.id)

    def test_get_grade_detail_existing_grade(self):
        """Test getting grade detail for existing grade."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        grade = GradeHistory.objects.create(
            student=self.user, exam=self.exam, session_id=session.id,
            status='COMPLETED', started_at=timezone.now()
        )

        result = GradingService.get_grade_detail(grade.id, self.user)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, grade.id)

    def test_get_grade_detail_nonexistent_grade(self):
        """Test getting grade detail for non-existent grade."""
        result = GradingService.get_grade_detail(99999, self.user)

        self.assertIsNone(result)

    def test_get_grade_detail_different_student(self):
        """Test student cannot access another student's grade."""
        other_user = create_test_user(email='other@example.com')
        session = ExamSession.objects.create(student=other_user, exam=self.exam)
        grade = GradeHistory.objects.create(
            student=other_user, exam=self.exam, session_id=session.id,
            status='COMPLETED', started_at=timezone.now()
        )

        result = GradingService.get_grade_detail(grade.id, self.user)

        self.assertIsNone(result)

    def test_grade_session_idempotent(self):
        """Test grading same session twice returns same grade history."""
        session = ExamSession.objects.create(student=self.user, exam=self.exam)
        StudentAnswer.objects.create(
            session=session, question=self.q1, answer_text='Answer'
        )

        grade1 = GradingService.grade_session(session)
        grade2 = GradingService.grade_session(session)

        self.assertEqual(grade1.id, grade2.id)

