"""Admin views for viewing sessions and grades."""
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.core.mixins import Custom404Mixin, StandardResponseListMixin, StandardResponseRetrieveMixin
from apps.assessments.models import Exam, ExamSession
from apps.core.permissions import IsAdmin
from apps.grading.models import GradeHistory
from apps.grading.serializers.admin_serializers import (
    AdminSessionListSerializer,
    AdminSessionDetailSerializer,
    AdminGradeListSerializer,
    AdminGradeDetailSerializer,
)

logger = logging.getLogger(__name__)


class AdminExamSessionsListView(StandardResponseListMixin, generics.ListAPIView):
    """List all sessions for an exam (admin only)."""
    serializer_class = AdminSessionListSerializer
    permission_classes = [IsAdmin]
    success_message = 'Sessions retrieved successfully'

    def get_queryset(self):
        exam_id = self.kwargs.get('exam_id')
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_sessions_for_exam(exam_id)

    @extend_schema(
        summary='List exam sessions',
        description='List all student sessions for a specific exam.',
        parameters=[
            OpenApiParameter('exam_id', int, location=OpenApiParameter.PATH, description='Exam ID'),
        ],
        responses={200: AdminSessionListSerializer(many=True)},
        tags=['Admin - Sessions']
    )
    def get(self, request, *args, **kwargs):
        from apps.assessments.services.exam_service import ExamService
        exam_id = self.kwargs.get('exam_id')
        if not ExamService.exam_exists(exam_id):
            return StandardResponse.not_found(message='Exam not found.')
        return super().get(request, *args, **kwargs)


class AdminSessionDetailView(Custom404Mixin, StandardResponseRetrieveMixin, generics.RetrieveAPIView):
    """View detailed session with all student answers (admin only)."""
    serializer_class = AdminSessionDetailSerializer
    permission_classes = [IsAdmin]
    not_found_message = 'Session not found.'
    success_message = 'Session details retrieved successfully'
    
    def get_queryset(self):
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_session_detail_queryset()

    @extend_schema(
        summary='View session details',
        description='View detailed session including all student answers and questions.',
        parameters=[
            OpenApiParameter('pk', int, location=OpenApiParameter.PATH, description='Session ID'),
        ],
        responses={200: AdminSessionDetailSerializer},
        tags=['Admin - Sessions']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminExamGradesListView(StandardResponseListMixin, generics.ListAPIView):
    """List all grades for an exam (admin only)."""
    serializer_class = AdminGradeListSerializer
    permission_classes = [IsAdmin]
    success_message = 'Grades retrieved successfully'

    def get_queryset(self):
        exam_id = self.kwargs.get('exam_id')
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_grades_for_exam(exam_id)

    @extend_schema(
        summary='List exam grades',
        description='List all graded submissions for a specific exam.',
        parameters=[
            OpenApiParameter('exam_id', int, location=OpenApiParameter.PATH, description='Exam ID'),
        ],
        responses={200: AdminGradeListSerializer(many=True)},
        tags=['Admin - Grades']
    )
    def get(self, request, *args, **kwargs):
        from apps.assessments.services.exam_service import ExamService
        exam_id = self.kwargs.get('exam_id')
        if not ExamService.exam_exists(exam_id):
            return StandardResponse.not_found(message='Exam not found.')
        return super().get(request, *args, **kwargs)


class AdminGradeDetailView(Custom404Mixin, StandardResponseRetrieveMixin, generics.RetrieveAPIView):
    """View detailed grade with full question/answer breakdown (admin only)."""
    serializer_class = AdminGradeDetailSerializer
    permission_classes = [IsAdmin]
    not_found_message = 'Grade not found.'
    success_message = 'Grade details retrieved successfully'
    
    def get_queryset(self):
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_grade_detail_queryset()

    @extend_schema(
        summary='View grade details',
        description='View detailed grade including full question payloads and student answers.',
        parameters=[
            OpenApiParameter('pk', int, location=OpenApiParameter.PATH, description='Grade History ID'),
        ],
        responses={200: AdminGradeDetailSerializer},
        tags=['Admin - Grades']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminAllGradesListView(StandardResponseListMixin, generics.ListAPIView):
    """List all grades across all exams (admin only)."""
    serializer_class = AdminGradeListSerializer
    permission_classes = [IsAdmin]
    success_message = 'Grades retrieved successfully'
    
    def get_queryset(self):
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_all_grades()

    @extend_schema(
        summary='List all grades',
        description='List all graded submissions across all exams.',
        responses={200: AdminGradeListSerializer(many=True)},
        tags=['Admin - Grades']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

