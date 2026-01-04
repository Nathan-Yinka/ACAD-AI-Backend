import logging
from apps.assessments.models import Exam

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

