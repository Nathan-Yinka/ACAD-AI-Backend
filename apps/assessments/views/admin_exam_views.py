"""
Admin exam views.
"""
import logging
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from apps.core.mixins import StandardResponseMixin
from apps.core.response import StandardResponse
from apps.assessments.models import Exam
from apps.assessments.serializers.admin_serializers import (
    AdminExamSerializer,
    AdminExamDetailSerializer,
)
from apps.core.permissions import IsAdmin
from apps.assessments.services.exam_service import ExamService
from apps.core.exceptions import ExamModificationError

logger = logging.getLogger(__name__)


@extend_schema_view(
    activate=extend_schema(
        summary='Activate exam',
        description='Make an exam active and available for students.',
        tags=['Admin - Exams']
    ),
    deactivate=extend_schema(
        summary='Deactivate exam',
        description='Make an exam inactive and unavailable for students.',
        tags=['Admin - Exams']
    ),
)
class AdminExamViewSet(StandardResponseMixin, viewsets.ModelViewSet):
    """Admin ViewSet for managing exams."""
    
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminExamDetailSerializer
        return AdminExamSerializer
    
    def get_queryset(self):
        return ExamService.get_all_exams()
    
    @extend_schema(
        summary='Update exam',
        description='Update exam details including making it active/inactive (admin only).',
        parameters=[
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
        ],
        tags=['Admin - Exams']
    )
    def update(self, request, *args, **kwargs):
        exam = self.get_object()
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot modify an exam that has active sessions or submissions.')
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary='Partially update exam',
        description='Partially update exam details (admin only).',
        parameters=[
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
        ],
        tags=['Admin - Exams']
    )
    def partial_update(self, request, *args, **kwargs):
        exam = self.get_object()
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot modify an exam that has active sessions or submissions.')
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary='Delete exam',
        description='Delete an exam (admin only).',
        parameters=[
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Exam ID', required=True),
        ],
        tags=['Admin - Exams']
    )
    def destroy(self, request, *args, **kwargs):
        exam = self.get_object()
        if exam.has_active_sessions() or exam.has_submissions():
            raise ExamModificationError('Cannot delete an exam that has active sessions or submissions.')
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        exam = self.get_object()
        if exam.get_questions_count() == 0:
            return StandardResponse.error(
                message='Cannot activate an exam without questions. Please add questions to the exam first.',
                status_code=400
            )
        exam.is_active = True
        exam.save(update_fields=['is_active'])
        return StandardResponse.success(
            data=AdminExamSerializer(exam).data,
            message='Exam activated successfully'
        )

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        exam = self.get_object()
        exam.is_active = False
        exam.save(update_fields=['is_active'])
        return StandardResponse.success(
            data=AdminExamSerializer(exam).data,
            message='Exam deactivated successfully'
        )

