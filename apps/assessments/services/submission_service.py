import logging
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from apps.assessments.models import Exam, Submission, Answer, Question
from apps.grading.services.graders import get_grading_service
from apps.assessments.services.answer_service import AnswerService
from apps.assessments.utils import is_exam_time_exceeded
from apps.core.exceptions import (
    ExamNotFoundError,
    SubmissionValidationError,
    TimeLimitExceededError,
    IncompleteSubmissionError,
    GradingError,
)

logger = logging.getLogger(__name__)


class SubmissionService:
    @staticmethod
    def validate_submission_data(exam_id: int, answers_data: list, student) -> Exam:
        """Validate submission data including exam existence and answer completeness."""
        logger.info(f'Validating submission data for exam {exam_id} by student {student.email}')
        try:
            exam = Exam.objects.prefetch_related('questions').get(
                id=exam_id,
                is_active=True
            )
        except Exam.DoesNotExist:
            logger.warning(f'Exam {exam_id} not found or inactive for student {student.email}')
            raise ExamNotFoundError('Exam not found or is not active.')
        
        exam_questions = exam.questions.all()
        question_ids = {q.id for q in exam_questions}
        submitted_question_ids = {ans['question_id'] for ans in answers_data}
        
        if question_ids != submitted_question_ids:
            missing_questions = question_ids - submitted_question_ids
            logger.warning(f'Incomplete submission for exam {exam_id} by student {student.email}. Missing questions: {missing_questions}')
            raise IncompleteSubmissionError(
                f'Missing answers for questions: {", ".join(map(str, missing_questions))}'
            )
        
        logger.info(f'Submission data validated successfully for exam {exam_id} by student {student.email}')
        return exam
    
    @staticmethod
    def check_time_limit(submission_start_time, exam: Exam) -> None:
        """Check if exam time limit has been exceeded."""
        if is_exam_time_exceeded(submission_start_time, exam.duration_minutes):
            raise TimeLimitExceededError(
                f'Exam time limit of {exam.duration_minutes} minutes has been exceeded.'
            )
    
    @staticmethod
    @transaction.atomic
    def create_submission(exam: Exam, answers_data: list, student, submission_start_time=None):
        """Create a new submission with normalized answers."""
        if submission_start_time:
            SubmissionService.check_time_limit(submission_start_time, exam)
        
        max_score = exam.get_max_score()
        
        submission = Submission.objects.create(
            student=student,
            exam=exam,
            max_score=max_score,
            status='PENDING'
        )
        
        question_map = {q.id: q for q in exam.questions.all()}
        
        for answer_data in answers_data:
            question_id = answer_data['question_id']
            question = question_map.get(question_id)
            
            if not question:
                raise SubmissionValidationError(f'Invalid question ID: {question_id}')
            
            raw_answer_text = answer_data['answer_text']
            normalized_answer_text = AnswerService.normalize_answer(question, raw_answer_text)
            
            Answer.objects.create(
                submission=submission,
                question=question,
                answer_text=normalized_answer_text
            )
        
        return submission
    
    @staticmethod
    @transaction.atomic
    def grade_submission(submission: Submission):
        """Grade a submission using the configured grading service."""
        logger.info(f'Starting grading for submission {submission.id} (exam {submission.exam.id})')
        try:
            grading_service = get_grading_service()
            logger.debug(f'Using grading service: {type(grading_service).__name__}')
            grading_result = grading_service.grade_submission(submission)
            
            submission.status = grading_result['status']
            submission.total_score = grading_result['total_score']
            submission.graded_at = timezone.now()
            submission.save()
            
            for answer_data in grading_result['answers']:
                answer = Answer.objects.get(id=answer_data['answer_id'])
                answer.score = answer_data['score']
                answer.graded_at = timezone.now()
                answer.save(update_fields=['score', 'graded_at'])
            
            submission.refresh_from_db()
            submission = Submission.objects.select_related(
                'student', 'exam'
            ).prefetch_related(
                'answers__question', 'exam__questions'
            ).get(id=submission.id)
            
            logger.info(f'Grading completed for submission {submission.id}. Score: {submission.total_score}/{submission.max_score}')
            return submission
            
        except Exception as e:
            logger.error(f'Grading failed for submission {submission.id}: {str(e)}', exc_info=True)
            submission.status = 'FAILED'
            submission.save(update_fields=['status'])
            raise GradingError(f'Grading failed: {str(e)}')
    
    @staticmethod
    def get_user_submissions(student):
        """Get all submissions for a student with optimized queries."""
        return Submission.objects.filter(
            student=student
        ).select_related(
            'exam', 'student'
        ).prefetch_related(
            'answers__question'
        )
    
    @staticmethod
    @transaction.atomic
    def submit_and_grade(exam_id: int, answers_data: list, student, submission_start_time=None):
        """Submit answers and automatically grade the submission."""
        exam = SubmissionService.validate_submission_data(exam_id, answers_data, student)
        submission = SubmissionService.create_submission(
            exam, answers_data, student, submission_start_time
        )
        
        try:
            submission = SubmissionService.grade_submission(submission)
        except GradingError:
            raise
        
        return submission

