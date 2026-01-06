"""Views for exam listing and session management."""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.core.mixins import StandardResponseMixin, Custom404Mixin
from apps.assessments.services.exam_service import ExamService
from apps.assessments.services.exam_session_service import ExamSessionService
from apps.assessments.serializers import (
    ExamListSerializer,
    ExamDetailSerializer,
)
from apps.assessments.serializers.session_serializers import ExamSessionWithTokenSerializer
from apps.core.permissions import IsStudent
from apps.core.exceptions import ExamNotFoundError

logger = logging.getLogger(__name__)


class ExamViewSet(StandardResponseMixin, Custom404Mixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing exams."""
    
    permission_classes = [permissions.IsAuthenticated]
    not_found_message = 'Exam not found.'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExamDetailSerializer
        return ExamListSerializer
    
    def get_queryset(self):
        return ExamService.get_active_exams()
    
    @extend_schema(
        summary='List active exams',
        description='Retrieve all active exams. Includes active session info and grade info if exists.',
        responses={200: ExamListSerializer(many=True)},
        tags=['Exams']
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        if hasattr(response, 'data') and 'data' in response.data:
            data = response.data['data']
            exam_ids = []
            exam_list = []
            
            if isinstance(data, dict) and 'results' in data:
                exam_list = data['results']
            elif isinstance(data, list):
                exam_list = data
            
            for exam_data in exam_list:
                exam_id = exam_data.get('id')
                if exam_id:
                    exam_ids.append(exam_id)
            
            if exam_ids:
                batch_info = ExamSessionService.get_batch_session_and_grade_info(
                    request.user, exam_ids
                )
                
                for exam_data in exam_list:
                    exam_id = exam_data.get('id')
                    if exam_id and exam_id in batch_info:
                        exam_data['active_session'] = batch_info[exam_id]['session_info']
                        exam_data['grade_info'] = batch_info[exam_id]['grade_info']
        
        return response
    
    @extend_schema(
        summary='Retrieve exam details',
        description='Get exam details (without questions). Shows active session and grade info if available.',
        parameters=[
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Exam ID'),
        ],
        responses={200: ExamDetailSerializer},
        tags=['Exams']
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().retrieve(request, *args, **kwargs)
        
        if hasattr(response, 'data') and isinstance(response.data, dict):
            exam_data = response.data.get('data') if 'data' in response.data else response.data
            
            session_info = ExamSessionService.get_active_session_info(
                request.user, instance.id
            )
            exam_data['active_session'] = session_info
            
            grade_info = ExamSessionService.get_grade_info(
                request.user, instance.id
            )
            exam_data['grade_info'] = grade_info
        
        return response
    
    @extend_schema(
        summary='Start or continue exam',
        description='Start a new exam session or continue existing one. Returns a new token each time.',
        parameters=[
            OpenApiParameter('id', int, location=OpenApiParameter.PATH, description='Exam ID'),
        ],
        responses={
            201: ExamSessionWithTokenSerializer,
            200: ExamSessionWithTokenSerializer,
            400: {'description': 'Exam already completed'},
        },
        tags=['Exams']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsStudent], url_path='start')
    def start(self, request, pk=None):
        """Start or continue an exam session. Returns new token."""
        exam = self.get_object()
        logger.info(f'Start/continue exam {exam.id} by {request.user.email}')
        
        try:
            session, token, action = ExamSessionService.start_or_continue_session(
                request.user, exam.id
            )
            serializer = ExamSessionWithTokenSerializer(session)
            
            message = 'Exam session started' if action == 'started' else 'Session continued with new token'
            status_code = status.HTTP_201_CREATED if action == 'started' else status.HTTP_200_OK
            
            return StandardResponse(
                data=serializer.data,
                message=message,
                status_code=status_code
            )
        except ValueError as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except ExamNotFoundError as e:
            return StandardResponse.not_found(message=str(e))
