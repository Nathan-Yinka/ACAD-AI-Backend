"""
Admin question views.
"""
import logging
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from apps.core.mixins import StandardResponseMixin
from apps.core.response import StandardResponse
from apps.assessments.models import Question, Exam
from apps.assessments.serializers.admin_serializers import AdminQuestionSerializer
from apps.assessments.services.question_service import QuestionService
from apps.core.permissions import IsAdmin
from apps.core.exceptions import ExamNotFoundError, ExamModificationError

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary='List questions for an exam',
        description='Retrieve all questions for a specific exam (admin only).',
        tags=['Admin - Questions']
    ),
    create=extend_schema(
        summary='Create question for an exam',
        description='Add a new question to an exam (admin only).',
        tags=['Admin - Questions']
    ),
    retrieve=extend_schema(
        summary='Retrieve question details',
        description='Retrieve detailed information about a specific question (admin only).',
        tags=['Admin - Questions']
    ),
)
class AdminQuestionViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """Admin ViewSet for managing questions within exams."""
    
    serializer_class = AdminQuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        exam_id = self.kwargs.get('exam_pk')
        if exam_id:
            return Question.objects.filter(exam_id=exam_id).order_by('order')
        return Question.objects.all()
    
    def perform_create(self, serializer):
        exam_id = self.kwargs.get('exam_pk')
        if not exam_id:
            raise ExamNotFoundError('Exam ID is required')
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise ExamNotFoundError('Exam not found')
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot add questions to an exam that has active sessions or submissions.')
        serializer.context['exam'] = exam
        serializer.save(exam=exam)
    
    @extend_schema(
        summary='Update question',
        description='Update question details (admin only).',
        parameters=[
            OpenApiParameter('exam_pk', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Question ID', required=True),
        ],
        tags=['Admin - Questions']
    )
    def update(self, request, *args, **kwargs):
        question = self.get_object()
        if question.exam.has_active_sessions() or question.exam.has_submissions():
            raise ExamModificationError('Cannot modify questions for an exam that has active sessions or submissions.')
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary='Partially update question',
        description='Partially update question details (admin only).',
        parameters=[
            OpenApiParameter('exam_pk', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Question ID', required=True),
        ],
        tags=['Admin - Questions']
    )
    def partial_update(self, request, *args, **kwargs):
        question = self.get_object()
        if question.exam.has_active_sessions() or question.exam.has_submissions():
            raise ExamModificationError('Cannot modify questions for an exam that has active sessions or submissions.')
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary='Delete question',
        description='Delete a question from an exam and reorder remaining questions (admin only).',
        parameters=[
            OpenApiParameter('exam_pk', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Question ID', required=True),
        ],
        tags=['Admin - Questions']
    )
    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        exam = question.exam
        
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot delete questions from an exam that has active sessions or submissions.')
        
        QuestionService.delete_question_and_reorder(question)
        
        return StandardResponse.success(message='Question deleted successfully and remaining questions reordered')

