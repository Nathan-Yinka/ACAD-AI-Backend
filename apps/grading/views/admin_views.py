"""Admin views for viewing sessions and grades."""
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.assessments.models import Exam, ExamSession
from apps.assessments.permissions import IsAdmin
from apps.grading.models import GradeHistory
from apps.grading.serializers.admin_serializers import (
    AdminSessionListSerializer,
    AdminSessionDetailSerializer,
    AdminGradeListSerializer,
    AdminGradeDetailSerializer,
)

logger = logging.getLogger(__name__)


class AdminExamSessionsListView(generics.ListAPIView):
    """List all sessions for an exam (admin only)."""
    serializer_class = AdminSessionListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        exam_id = self.kwargs.get('exam_id')
        return ExamSession.objects.filter(
            exam_id=exam_id
        ).select_related('student', 'exam').order_by('-started_at')

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
        # Verify exam exists
        exam_id = self.kwargs.get('exam_id')
        if not Exam.objects.filter(id=exam_id).exists():
            return StandardResponse.not_found(message='Exam not found.')
        
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Sessions retrieved successfully'
        )


class AdminSessionDetailView(generics.RetrieveAPIView):
    """View detailed session with all student answers (admin only)."""
    serializer_class = AdminSessionDetailSerializer
    permission_classes = [IsAdmin]
    queryset = ExamSession.objects.select_related(
        'student', 'exam'
    ).prefetch_related('student_answers__question')

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
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Session details retrieved successfully'
        )


class AdminExamGradesListView(generics.ListAPIView):
    """List all grades for an exam (admin only)."""
    serializer_class = AdminGradeListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        exam_id = self.kwargs.get('exam_id')
        return GradeHistory.objects.filter(
            exam_id=exam_id
        ).select_related('student', 'exam').order_by('-created_at')

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
        exam_id = self.kwargs.get('exam_id')
        if not Exam.objects.filter(id=exam_id).exists():
            return StandardResponse.not_found(message='Exam not found.')
        
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Grades retrieved successfully'
        )


class AdminGradeDetailView(generics.RetrieveAPIView):
    """View detailed grade with full question/answer breakdown (admin only)."""
    serializer_class = AdminGradeDetailSerializer
    permission_classes = [IsAdmin]
    queryset = GradeHistory.objects.select_related('student', 'exam')

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
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Grade details retrieved successfully'
        )


class AdminAllGradesListView(generics.ListAPIView):
    """List all grades across all exams (admin only)."""
    serializer_class = AdminGradeListSerializer
    permission_classes = [IsAdmin]
    queryset = GradeHistory.objects.select_related('student', 'exam').order_by('-created_at')

    @extend_schema(
        summary='List all grades',
        description='List all graded submissions across all exams.',
        responses={200: AdminGradeListSerializer(many=True)},
        tags=['Admin - Grades']
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Grades retrieved successfully'
        )

