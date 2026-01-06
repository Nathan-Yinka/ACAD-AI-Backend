"""Service for handling exam operations."""
import logging
from apps.assessments.models import Exam
from apps.core.exceptions import ExamModificationError

logger = logging.getLogger(__name__)


class ExamService:
    @staticmethod
    def get_active_exams():
        """Return all active exams with prefetched questions."""
        return Exam.objects.filter(is_active=True).prefetch_related('questions')
    
    @staticmethod
    def get_exam_by_id(exam_id: int, include_questions: bool = True):
        """Get exam by ID, optionally with prefetched questions."""
        queryset = Exam.objects.all()
        if include_questions:
            queryset = queryset.prefetch_related('questions')
        return queryset.get(id=exam_id, is_active=True)
    
    @staticmethod
    def get_all_exams():
        """Return all exams with prefetched questions (admin only)."""
        return Exam.objects.prefetch_related('questions').all()
    
    @staticmethod
    def get_exam_by_id_or_none(exam_id: int):
        """Get exam by ID, returns None if not found."""
        try:
            return Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return None
    
    @staticmethod
    def exam_exists(exam_id: int) -> bool:
        """Check if exam exists."""
        return Exam.objects.filter(id=exam_id).exists()
    
    @staticmethod
    def validate_exam_modification(exam: Exam):
        """Validate that exam can be modified (no active sessions or submissions)."""
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot modify an exam that has active sessions or submissions.')
    
    @staticmethod
    def activate_exam(exam: Exam):
        """Activate an exam. Raises ValueError if exam has no questions."""
        if exam.get_questions_count() == 0:
            raise ValueError('Cannot activate an exam without questions. Please add questions to the exam first.')
        exam.is_active = True
        exam.save(update_fields=['is_active'])
        logger.info(f'Exam {exam.id} activated')
    
    @staticmethod
    def deactivate_exam(exam: Exam):
        """Deactivate an exam."""
        exam.is_active = False
        exam.save(update_fields=['is_active'])
        logger.info(f'Exam {exam.id} deactivated')

