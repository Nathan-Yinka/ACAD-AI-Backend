"""Views for student grade history."""
import logging
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.core.mixins import Custom404Mixin, StandardResponseListMixin, StandardResponseRetrieveMixin
from apps.grading.models import GradeHistory
from apps.grading.serializers.grade_serializers import GradeHistoryListSerializer, GradeHistoryDetailSerializer
from apps.core.permissions import IsStudent

logger = logging.getLogger(__name__)


class GradeHistoryListView(StandardResponseListMixin, generics.ListAPIView):
    """List grade history for the authenticated student."""
    serializer_class = GradeHistoryListSerializer
    permission_classes = [IsStudent]
    success_message = 'Grade history retrieved successfully'

    def get_queryset(self):
        """Return grade history for the current user."""
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_student_grade_history(self.request.user)

    @extend_schema(
        summary='List grade history',
        description='Retrieve all grade history entries for the authenticated student.',
        responses={200: GradeHistoryListSerializer(many=True)},
        tags=['Grades']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class GradeHistoryDetailView(Custom404Mixin, StandardResponseRetrieveMixin, generics.RetrieveAPIView):
    """Retrieve detailed grade history entry."""
    serializer_class = GradeHistoryDetailSerializer
    permission_classes = [IsStudent]
    not_found_message = 'Grade not found.'
    success_message = 'Grade detail retrieved successfully'

    def get_queryset(self):
        """Return grade history for the current user."""
        from apps.grading.services.grading_service import GradingService
        return GradingService.get_student_grade_history(self.request.user)

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
        return super().get(request, *args, **kwargs)

