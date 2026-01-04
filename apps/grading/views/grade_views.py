"""Views for student grade history."""
import logging
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.grading.models import GradeHistory
from apps.grading.serializers.grade_serializers import GradeHistoryListSerializer, GradeHistoryDetailSerializer
from apps.assessments.permissions import IsStudent

logger = logging.getLogger(__name__)


class GradeHistoryListView(generics.ListAPIView):
    """List grade history for the authenticated student."""
    serializer_class = GradeHistoryListSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        """Return grade history for the current user."""
        return GradeHistory.objects.filter(
            student=self.request.user
        ).select_related('exam').order_by('-created_at')

    @extend_schema(
        summary='List grade history',
        description='Retrieve all grade history entries for the authenticated student.',
        responses={200: GradeHistoryListSerializer(many=True)},
        tags=['Grades']
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Grade history retrieved successfully'
        )


class GradeHistoryDetailView(generics.RetrieveAPIView):
    """Retrieve detailed grade history entry."""
    serializer_class = GradeHistoryDetailSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        """Return grade history for the current user."""
        return GradeHistory.objects.filter(
            student=self.request.user
        ).select_related('exam')

    @extend_schema(
        summary='Get grade detail',
        description='Retrieve detailed information about a specific grade history entry.',
        parameters=[
            OpenApiParameter('pk', int, location=OpenApiParameter.PATH, description='Grade History ID'),
        ],
        responses={
            200: GradeHistoryDetailSerializer,
            404: {'description': 'Grade not found'},
        },
        tags=['Grades']
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return StandardResponse.success(
            data=response.data,
            message='Grade detail retrieved successfully'
        )

