"""Tests for assessments services."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.core.test_utils import create_test_user, create_test_admin
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer, Submission
from apps.assessments.services.exam_session_service import ExamSessionService
from apps.assessments.services.exam_service import ExamService
from apps.assessments.services.question_service import QuestionService
from apps.assessments.services.answer_service import AnswerService
from apps.core.exceptions import ExamNotFoundError, SubmissionValidationError, ExamModificationError
from apps.grading.models import GradeHistory


class ExamSessionServiceTests(TestCase):
    """Tests for ExamSessionService."""

    def setUp(self):
        self.user = create_test_user(email='student@example.com')
        self.admin = create_test_admin(email='admin@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)

    def test_start_new_session(self):
        """Test starting a new session."""
        session, token, action = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )

        self.assertEqual(action, 'started')
        self.assertEqual(session.student, self.user)
        self.assertEqual(session.exam, self.exam)
        self.assertIsNotNone(token)

    def test_continue_existing_session(self):
        """Test continuing an existing session."""
        session1, token1, _ = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )
        session2, token2, action = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )

        self.assertEqual(action, 'continued')
        self.assertEqual(session1.id, session2.id)  # Same session
        self.assertNotEqual(token1.token, token2.token)  # Different token

        # Old token should be invalid
        token1.refresh_from_db()
        self.assertFalse(token1.is_valid)

    def test_start_session_inactive_exam(self):
        """Test starting session for inactive exam raises error."""
        self.exam.is_active = False
        self.exam.save()

        with self.assertRaises(ExamNotFoundError):
            ExamSessionService.start_or_continue_session(self.user, self.exam.id)

    def test_start_completed_session_raises_error(self):
        """Test cannot restart completed session."""
        session, _, _ = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )
        session.mark_completed()

        with self.assertRaises(ValueError):
            ExamSessionService.start_or_continue_session(self.user, self.exam.id)

    def test_validate_token(self):
        """Test token validation."""
        session, token, _ = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )

        validated_session, validated_token = ExamSessionService.validate_token(
            token.token, self.user
        )

        self.assertEqual(validated_session.id, session.id)
        self.assertEqual(validated_token.id, token.id)

    def test_validate_token_wrong_user(self):
        """Test token validation fails for wrong user."""
        other_user = create_test_user(email='other@example.com')
        _, token, _ = ExamSessionService.start_or_continue_session(
            self.user, self.exam.id
        )

        with self.assertRaises(ValueError):
            ExamSessionService.validate_token(token.token, other_user)

    def test_validate_invalid_token(self):
        """Test validation with invalid token."""
        with self.assertRaises(ValueError):
            ExamSessionService.validate_token('invalid-token', self.user)

    def test_get_active_session_info(self):
        """Test getting active session info for exam listing."""
        ExamSessionService.start_or_continue_session(self.user, self.exam.id)

        info = ExamSessionService.get_active_session_info(self.user, self.exam.id)

        self.assertIsNotNone(info)
        self.assertIn('time_remaining_seconds', info)
        self.assertIn('answered_count', info)

    def test_get_batch_session_and_grade_info(self):
        """Test batch fetching session and grade info for multiple exams."""
        exam2 = Exam.objects.create(
            title='Test Exam 2',
            course='TEST102',
            duration_minutes=30,
            is_active=True
        )
        Question.objects.create(exam=exam2, order=1, question_text='Q1', expected_answer='Answer', points=10)

        session1, _, _ = ExamSessionService.start_or_continue_session(self.user, self.exam.id)
        session2, _, _ = ExamSessionService.start_or_continue_session(self.user, exam2.id)

        batch_info = ExamSessionService.get_batch_session_and_grade_info(
            self.user, [self.exam.id, exam2.id]
        )

        self.assertEqual(len(batch_info), 2)
        self.assertIn(self.exam.id, batch_info)
        self.assertIn(exam2.id, batch_info)
        self.assertIsNotNone(batch_info[self.exam.id]['session_info'])
        self.assertIsNotNone(batch_info[exam2.id]['session_info'])
        self.assertIsNone(batch_info[self.exam.id]['grade_info'])
        self.assertIsNone(batch_info[exam2.id]['grade_info'])

    def test_get_batch_session_and_grade_info_with_grades(self):
        """Test batch fetching includes grade info when grades exist."""
        session, _, _ = ExamSessionService.start_or_continue_session(self.user, self.exam.id)
        session.mark_completed()

        grade = GradeHistory.objects.create(
            student=self.user,
            exam=self.exam,
            session_id=session.id,
            status='COMPLETED',
            total_score=10.0,
            max_score=10.0,
            percentage=100.0,
            started_at=session.started_at
        )

        batch_info = ExamSessionService.get_batch_session_and_grade_info(
            self.user, [self.exam.id]
        )

        self.assertIsNotNone(batch_info[self.exam.id]['grade_info'])
        self.assertEqual(batch_info[self.exam.id]['grade_info']['grade_id'], grade.id)
        self.assertEqual(batch_info[self.exam.id]['grade_info']['total_score'], 10.0)

    def test_get_batch_session_and_grade_info_empty_list(self):
        """Test batch fetching with empty exam list returns empty dict."""
        batch_info = ExamSessionService.get_batch_session_and_grade_info(self.user, [])
        self.assertEqual(batch_info, {})

    def test_get_batch_session_and_grade_info_no_sessions(self):
        """Test batch fetching when no sessions exist."""
        batch_info = ExamSessionService.get_batch_session_and_grade_info(
            self.user, [self.exam.id]
        )
        self.assertEqual(batch_info[self.exam.id]['session_info'], None)
        self.assertEqual(batch_info[self.exam.id]['grade_info'], None)


class QuestionServiceTests(TestCase):
    """Tests for QuestionService."""

    def setUp(self):
        self.user = create_test_user(email='student2@example.com')
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=True
        )
        self.q1 = Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            question_type='SHORT_ANSWER', expected_answer='Answer', points=10
        )
        self.q2 = Question.objects.create(
            exam=self.exam, order=2, question_text='Q2',
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            expected_answer='opt1',
            points=5
        )
        self.session = ExamSession.objects.create(student=self.user, exam=self.exam)

    def test_get_question_by_order(self):
        """Test fetching question by order."""
        question = QuestionService.get_question_by_order(self.session, 1)
        self.assertEqual(question.id, self.q1.id)

    def test_get_question_updates_current_order(self):
        """Test fetching question updates session's current order."""
        QuestionService.get_question_by_order(self.session, 2)
        self.session.refresh_from_db()
        self.assertEqual(self.session.current_question_order, 2)

    def test_get_question_invalid_order(self):
        """Test fetching invalid question order raises error."""
        with self.assertRaises(ExamNotFoundError):
            QuestionService.get_question_by_order(self.session, 99)

    def test_get_question_expired_session(self):
        """Test fetching question from expired session raises error."""
        self.session.expires_at = timezone.now() - timedelta(minutes=1)
        self.session.save()

        with self.assertRaises(SubmissionValidationError):
            QuestionService.get_question_by_order(self.session, 1)

    def test_submit_single_answer(self):
        """Test submitting a single answer."""
        answer = QuestionService.submit_single_answer(self.session, 1, 'My answer')

        self.assertEqual(answer.answer_text, 'My answer')
        self.assertEqual(answer.session, self.session)
        self.assertEqual(answer.question, self.q1)

    def test_submit_answer_updates_existing(self):
        """Test submitting answer updates existing answer."""
        QuestionService.submit_single_answer(self.session, 1, 'First answer')
        answer = QuestionService.submit_single_answer(self.session, 1, 'Updated answer')

        self.assertEqual(answer.answer_text, 'Updated answer')
        self.assertEqual(StudentAnswer.objects.filter(session=self.session, question=self.q1).count(), 1)

    def test_get_session_progress(self):
        """Test getting session progress."""
        QuestionService.submit_single_answer(self.session, 1, 'Answer 1')

        progress = QuestionService.get_session_progress(self.session)

        self.assertEqual(progress['total_questions'], 2)
        self.assertEqual(progress['answered_count'], 1)
        self.assertEqual(progress['answered_questions'], [1])

    def test_get_answer_for_question(self):
        """Test getting saved answer for a question."""
        QuestionService.submit_single_answer(self.session, 1, 'My answer')

        saved = QuestionService.get_answer_for_question(self.session, 1)
        self.assertEqual(saved, 'My answer')

        not_answered = QuestionService.get_answer_for_question(self.session, 2)
        self.assertIsNone(not_answered)

    def test_delete_question_and_reorder(self):
        """Test deleting a question and reordering remaining questions."""
        q3 = Question.objects.create(
            exam=self.exam, order=3, question_text='Q3',
            question_type='SHORT_ANSWER', expected_answer='Answer', points=5
        )
        
        QuestionService.delete_question_and_reorder(self.q1)
        
        self.q2.refresh_from_db()
        q3.refresh_from_db()
        self.assertEqual(self.q2.order, 1)
        self.assertEqual(q3.order, 2)
        self.assertFalse(Question.objects.filter(id=self.q1.id).exists())

    def test_delete_question_and_reorder_maintains_sequence(self):
        """Test deleting question maintains sequential order without gaps."""
        q3 = Question.objects.create(
            exam=self.exam, order=3, question_text='Q3',
            question_type='SHORT_ANSWER', expected_answer='Answer', points=5
        )
        q4 = Question.objects.create(
            exam=self.exam, order=4, question_text='Q4',
            question_type='SHORT_ANSWER', expected_answer='Answer', points=5
        )
        
        QuestionService.delete_question_and_reorder(self.q2)
        
        self.q1.refresh_from_db()
        q3.refresh_from_db()
        q4.refresh_from_db()
        self.assertEqual(self.q1.order, 1)
        self.assertEqual(q3.order, 2)
        self.assertEqual(q4.order, 3)

    def test_validate_exam_for_question_modification_with_active_sessions(self):
        """Test validation fails when exam has active sessions."""
        user = create_test_user()
        self.exam.is_active = True
        self.exam.save()
        
        session, _, _ = ExamSessionService.start_or_continue_session(user, self.exam.id)
        
        with self.assertRaises(ExamModificationError):
            QuestionService.validate_exam_for_question_modification(self.exam)

    def test_get_exam_for_question_creation_success(self):
        """Test getting exam for question creation when valid."""
        exam2 = Exam.objects.create(
            title='Test Exam 2',
            course='TEST102',
            duration_minutes=30,
            is_active=False
        )
        exam = QuestionService.get_exam_for_question_creation(exam2.id)
        self.assertEqual(exam.id, exam2.id)

    def test_get_exam_for_question_creation_missing_id(self):
        """Test getting exam for question creation with missing ID raises error."""
        with self.assertRaises(ExamNotFoundError):
            QuestionService.get_exam_for_question_creation(None)

    def test_get_exam_for_question_creation_not_found(self):
        """Test getting exam for question creation when exam doesn't exist."""
        with self.assertRaises(ExamNotFoundError):
            QuestionService.get_exam_for_question_creation(99999)

    def test_get_exam_for_question_creation_with_active_sessions(self):
        """Test getting exam for question creation fails when exam has active sessions."""
        user = create_test_user()
        self.exam.is_active = True
        self.exam.save()
        
        session, _, _ = ExamSessionService.start_or_continue_session(user, self.exam.id)
        
        with self.assertRaises(ExamModificationError):
            QuestionService.get_exam_for_question_creation(self.exam.id)

    def test_get_questions_for_exam(self):
        """Test getting questions for a specific exam."""
        questions = QuestionService.get_questions_for_exam(self.exam.id)
        self.assertEqual(questions.count(), 2)
        self.assertEqual(list(questions.values_list('order', flat=True)), [1, 2])

    def test_get_questions_for_exam_all(self):
        """Test getting all questions when exam_id is None."""
        exam2 = Exam.objects.create(
            title='Test Exam 2',
            course='TEST102',
            duration_minutes=30,
            is_active=True
        )
        Question.objects.create(exam=exam2, order=1, question_text='Q1', expected_answer='Answer', points=10)
        
        questions = QuestionService.get_questions_for_exam(None)
        self.assertEqual(questions.count(), 3)


class AnswerServiceTests(TestCase):
    """Tests for AnswerService."""

    def setUp(self):
        self.exam = Exam.objects.create(title='Test', course='T101', duration_minutes=30)
        self.short_answer = Question.objects.create(
            exam=self.exam, order=1, question_text='Q1',
            question_type='SHORT_ANSWER', expected_answer='Expected Answer', points=10
        )
        self.mcq = Question.objects.create(
            exam=self.exam, order=2, question_text='Q2',
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            expected_answer='opt1',
            points=5
        )
        self.multi_select = Question.objects.create(
            exam=self.exam, order=3, question_text='Q3',
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'}
            ],
            expected_answer='["opt1", "opt3"]',
            allow_multiple=True,
            points=10
        )

    def test_normalize_short_answer(self):
        """Test normalizing short answer - preserves whitespace."""
        normalized = AnswerService.normalize_answer(self.short_answer, 'My Answer')
        self.assertEqual(normalized, 'My Answer')

    def test_normalize_mcq_single(self):
        """Test normalizing single-select MCQ answer."""
        normalized = AnswerService.normalize_answer(self.mcq, 'opt1')
        self.assertEqual(normalized, 'opt1')

    def test_normalize_mcq_multi(self):
        """Test normalizing multi-select MCQ answer (single option submitted)."""
        normalized = AnswerService.normalize_answer(self.multi_select, 'opt1')
        self.assertEqual(normalized, 'opt1')


class ExamServiceTests(TestCase):
    """Tests for ExamService."""

    def setUp(self):
        self.admin = create_test_admin()
        self.exam = Exam.objects.create(
            title='Test Exam',
            course='TEST101',
            duration_minutes=60,
            is_active=False
        )

    def test_activate_exam(self):
        """Test activating an exam."""
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)
        
        ExamService.activate_exam(self.exam)
        
        self.exam.refresh_from_db()
        self.assertTrue(self.exam.is_active)

    def test_activate_exam_without_questions_raises_error(self):
        """Test activating exam without questions raises ValueError."""
        with self.assertRaises(ValueError) as context:
            ExamService.activate_exam(self.exam)
        
        self.assertIn('without questions', str(context.exception))

    def test_deactivate_exam(self):
        """Test deactivating an exam."""
        self.exam.is_active = True
        self.exam.save()
        
        ExamService.deactivate_exam(self.exam)
        
        self.exam.refresh_from_db()
        self.assertFalse(self.exam.is_active)

    def test_validate_exam_modification_with_active_sessions(self):
        """Test validation fails when exam has active sessions."""
        user = create_test_user()
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)
        self.exam.is_active = True
        self.exam.save()
        
        session, _, _ = ExamSessionService.start_or_continue_session(user, self.exam.id)
        
        with self.assertRaises(ExamModificationError):
            ExamService.validate_exam_modification(self.exam)

    def test_validate_exam_modification_with_submissions(self):
        """Test validation fails when exam has submissions."""
        user = create_test_user()
        Question.objects.create(exam=self.exam, order=1, question_text='Q1', expected_answer='Answer', points=10)
        self.exam.is_active = True
        self.exam.save()
        
        Submission.objects.create(
            student=user,
            exam=self.exam,
            total_score=10.0,
            max_score=10.0,
            status='GRADED'
        )
        
        with self.assertRaises(ExamModificationError):
            ExamService.validate_exam_modification(self.exam)

    def test_validate_exam_modification_success(self):
        """Test validation succeeds when exam has no active sessions or submissions."""
        ExamService.validate_exam_modification(self.exam)

    def test_get_exam_by_id_or_none_exists(self):
        """Test getting exam by ID when it exists."""
        exam = ExamService.get_exam_by_id_or_none(self.exam.id)
        self.assertEqual(exam.id, self.exam.id)

    def test_get_exam_by_id_or_none_not_exists(self):
        """Test getting exam by ID when it doesn't exist returns None."""
        exam = ExamService.get_exam_by_id_or_none(99999)
        self.assertIsNone(exam)

    def test_exam_exists(self):
        """Test checking if exam exists."""
        self.assertTrue(ExamService.exam_exists(self.exam.id))
        self.assertFalse(ExamService.exam_exists(99999))
