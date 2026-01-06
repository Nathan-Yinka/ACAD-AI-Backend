"""Service for handling question operations during exam sessions."""
import logging
from django.db import transaction
from apps.assessments.models import Question, ExamSession, StudentAnswer, Exam
from apps.assessments.services.answer_service import AnswerService
from apps.core.exceptions import ExamNotFoundError, SubmissionValidationError, ExamModificationError

logger = logging.getLogger(__name__)


class QuestionService:
    @staticmethod
    def get_question_by_order(session: ExamSession, order: int) -> Question:
        """Get a specific question by order number for a session."""
        if session.is_completed:
            raise SubmissionValidationError('This exam session has already been completed.')
        
        if session.is_expired():
            raise SubmissionValidationError('This exam session has expired.')
        
        try:
            question = Question.objects.get(exam=session.exam, order=order)
            session.current_question_order = order
            session.save(update_fields=['current_question_order'])
            return question
        except Question.DoesNotExist:
            raise ExamNotFoundError(f'Question {order} not found in this exam.')

    @staticmethod
    @transaction.atomic
    def delete_question_and_reorder(question: Question):
        """
        Delete a question and reorder remaining questions for the exam.
        """
        exam = question.exam
        question.delete()
        
        remaining_questions = Question.objects.filter(exam=exam).order_by('order')
        for index, q in enumerate(remaining_questions, start=1):
            if q.order != index:
                q.order = index
                q.save(update_fields=['order'])
    
    @staticmethod
    def validate_answer_text(answer_text: str):
        """Validate that answer text is provided."""
        if not answer_text:
            raise SubmissionValidationError('Answer text is required.')
    
    @staticmethod
    def submit_single_answer(session: ExamSession, question_order: int, answer_text: str) -> StudentAnswer:
        """Submit an answer for a single question during an exam session."""
        QuestionService.validate_answer_text(answer_text)
        
        if session.is_completed:
            raise SubmissionValidationError('This exam session has already been completed.')
        
        if session.is_expired():
            raise SubmissionValidationError('This exam session has expired.')
        
        try:
            question = Question.objects.get(exam=session.exam, order=question_order)
        except Question.DoesNotExist:
            raise ExamNotFoundError(f'Question {question_order} not found in this exam.')
        
        normalized_answer = AnswerService.normalize_answer(question, answer_text)
        
        student_answer, created = StudentAnswer.objects.update_or_create(
            session=session,
            question=question,
            defaults={'answer_text': normalized_answer}
        )
        
        logger.info(f'Answer {"created" if created else "updated"} for session {session.id}, question {question_order}')
        return student_answer

    @staticmethod
    def get_session_progress(session: ExamSession) -> dict:
        """Get progress info for an exam session."""
        total_questions = session.get_total_questions()
        answered_count = session.get_answered_count()
        
        answered_questions = list(
            session.student_answers.values_list('question__order', flat=True)
        )
        
        return {
            'total_questions': total_questions,
            'answered_count': answered_count,
            'answered_questions': answered_questions,
            'current_question': session.current_question_order,
            'time_remaining_seconds': session.time_remaining_seconds(),
            'is_expired': session.is_expired(),
        }

    @staticmethod
    def get_answer_for_question(session: ExamSession, question_order: int) -> str:
        """Get the saved answer for a question in a session, if any."""
        try:
            answer = StudentAnswer.objects.get(
                session=session,
                question__order=question_order
            )
            return answer.answer_text
        except StudentAnswer.DoesNotExist:
            return None
    
    @staticmethod
    def get_questions_for_exam(exam_id: int = None):
        """Get all questions for an exam ordered by order field. If exam_id is None, returns all questions."""
        if exam_id:
            return Question.objects.filter(exam_id=exam_id).order_by('order')
        return Question.objects.all().order_by('order')
    
    @staticmethod
    def validate_exam_for_question_modification(exam: Exam):
        """Validate that exam can have questions added/modified."""
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot modify questions for an exam that has active sessions or submissions.')
    
    @staticmethod
    def get_exam_for_question_creation(exam_id: int) -> Exam:
        """
        Get and validate exam for question creation.
        Raises ExamNotFoundError if exam_id is missing or exam doesn't exist.
        Raises ExamModificationError if exam cannot be modified.
        """
        from apps.assessments.services.exam_service import ExamService
        from apps.core.exceptions import ExamNotFoundError
        
        if not exam_id:
            raise ExamNotFoundError('Exam ID is required')
        
        exam = ExamService.get_exam_by_id_or_none(exam_id)
        if not exam:
            raise ExamNotFoundError('Exam not found')
        
        QuestionService.validate_exam_for_question_modification(exam)
        return exam

