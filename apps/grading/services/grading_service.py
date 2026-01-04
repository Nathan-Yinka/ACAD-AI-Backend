"""Service for handling grading operations."""
import logging
from django.utils import timezone
from django.db import transaction
from apps.assessments.models import ExamSession, StudentAnswer, Submission, Answer
from apps.grading.services.graders import get_grading_service
from apps.grading.models import GradeHistory
from apps.core.exceptions import GradingError

logger = logging.getLogger(__name__)


class GradingService:
    @staticmethod
    @transaction.atomic
    def grade_session(session: ExamSession, grading_method: str = 'auto') -> GradeHistory:
        """Grade an exam session and create grade history."""
        if session.is_completed and grading_method != 'expired':
            existing = GradeHistory.objects.filter(session_id=session.id).first()
            if existing:
                return existing

        logger.info(f'Starting grading for session {session.id} (method: {grading_method})')
        
        grade_history = GradeHistory.objects.create(
            student=session.student,
            exam=session.exam,
            session_id=session.id,
            status='IN_PROGRESS',
            max_score=session.exam.get_max_score(),
            started_at=session.started_at,
            submitted_at=session.submitted_at or timezone.now(),
            grading_method=grading_method,
        )

        try:
            submission = Submission.objects.create(
                student=session.student,
                exam=session.exam,
                max_score=session.exam.get_max_score(),
                status='PENDING'
            )

            student_answers = session.student_answers.select_related('question').all()
            answers_data = []
            
            for sa in student_answers:
                question = sa.question
                answer = Answer.objects.create(
                    submission=submission,
                    question=question,
                    answer_text=sa.answer_text
                )
                # Store full question data for admin viewing
                answers_data.append({
                    'question_id': question.id,
                    'question_order': question.order,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'expected_answer': question.expected_answer,
                    'options': question.options,
                    'student_answer': sa.answer_text,
                    'answer_id': answer.id,
                    'max_score': float(question.points),
                })

            grading_service = get_grading_service()
            grading_result = grading_service.grade_submission(submission)

            submission.status = grading_result['status']
            submission.total_score = grading_result['total_score']
            submission.graded_at = timezone.now()
            submission.save()

            for answer_result in grading_result['answers']:
                answer = Answer.objects.get(id=answer_result['answer_id'])
                answer.score = answer_result['score']
                answer.graded_at = timezone.now()
                answer.save(update_fields=['score', 'graded_at'])
                
                for ad in answers_data:
                    if ad['answer_id'] == answer_result['answer_id']:
                        ad['score'] = float(answer_result['score'])
                        ad['feedback'] = answer_result.get('feedback', '')

            grade_history.total_score = submission.total_score
            grade_history.percentage = grade_history.calculate_percentage()
            grade_history.answers_data = answers_data
            grade_history.graded_at = timezone.now()
            grade_history.status = 'COMPLETED'
            grade_history.save()

            if not session.is_completed:
                session.mark_completed(
                    submission_type='AUTO_EXPIRED' if grading_method == 'expired' else 'MANUAL'
                )

            logger.info(f'Grading completed for session {session.id}. Score: {grade_history.total_score}/{grade_history.max_score}')
            return grade_history

        except Exception as e:
            logger.error(f'Grading failed for session {session.id}: {str(e)}', exc_info=True)
            grade_history.status = 'FAILED'
            grade_history.save()
            raise GradingError(f'Grading failed: {str(e)}')

    @staticmethod
    def get_grade_history(student, exam_id: int = None) -> list:
        """Get grade history for a student."""
        queryset = GradeHistory.objects.filter(student=student).select_related('exam')
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        return queryset

    @staticmethod
    def get_grade_detail(grade_id: int, student) -> GradeHistory:
        """Get detailed grade history entry."""
        try:
            return GradeHistory.objects.select_related('exam').get(id=grade_id, student=student)
        except GradeHistory.DoesNotExist:
            return None

