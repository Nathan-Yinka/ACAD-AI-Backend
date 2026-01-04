"""Views for single question fetch and answer submission using session tokens."""
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.core.response import StandardResponse
from apps.assessments.serializers import (
    QuestionDetailSerializer,
    SessionSubmitResponseSerializer,
    AnswerSubmitResponseSerializer,
    ProgressResponseSerializer,
)
from apps.assessments.services.question_service import QuestionService
from apps.assessments.services.exam_session_service import ExamSessionService
from apps.assessments.permissions import IsStudent
from apps.core.exceptions import ExamNotFoundError, SubmissionValidationError

logger = logging.getLogger(__name__)


class SessionQuestionView(generics.GenericAPIView):
    """Get a single question by order using session token."""
    permission_classes = [IsStudent]
    serializer_class = QuestionDetailSerializer

    @extend_schema(
        summary='Get single question',
        description='Fetch a specific question by order number using session token.',
        parameters=[
            OpenApiParameter('token', str, location=OpenApiParameter.PATH, description='Session Token'),
            OpenApiParameter('order', int, location=OpenApiParameter.PATH, description='Question order'),
        ],
        responses={200: QuestionDetailSerializer},
        tags=['Exam Session']
    )
    def get(self, request, token, order):
        try:
            session, token_obj = ExamSessionService.validate_token(token, request.user)
        except ValueError as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        try:
            question = QuestionService.get_question_by_order(session, order)
            saved_answer = QuestionService.get_answer_for_question(session, order)
            progress = QuestionService.get_session_progress(session)
            
            serializer = QuestionDetailSerializer(question)
            data = serializer.data
            data['saved_answer'] = saved_answer
            data['progress'] = progress
            
            return StandardResponse.success(data=data, message='Question retrieved successfully')
        except (ExamNotFoundError, SubmissionValidationError) as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


class SessionAnswerView(generics.GenericAPIView):
    """Submit an answer for a single question using session token."""
    permission_classes = [IsStudent]
    serializer_class = AnswerSubmitResponseSerializer

    @extend_schema(
        summary='Submit single answer',
        description='Submit an answer for a specific question using session token.',
        parameters=[
            OpenApiParameter('token', str, location=OpenApiParameter.PATH, description='Session Token'),
            OpenApiParameter('order', int, location=OpenApiParameter.PATH, description='Question order'),
        ],
        request={'application/json': {'type': 'object', 'properties': {'answer_text': {'type': 'string'}}}},
        responses={200: AnswerSubmitResponseSerializer},
        tags=['Exam Session']
    )
    def post(self, request, token, order):
        try:
            session, token_obj = ExamSessionService.validate_token(token, request.user)
        except ValueError as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        answer_text = request.data.get('answer_text', '')
        if not answer_text:
            return StandardResponse.validation_error(message='Answer text is required.')

        try:
            student_answer = QuestionService.submit_single_answer(session, order, answer_text)
            progress = QuestionService.get_session_progress(session)
            
            return StandardResponse.success(
                data={
                    'question_order': order,
                    'answer_text': student_answer.answer_text,
                    'answered_at': student_answer.answered_at.isoformat(),
                    'progress': progress,
                },
                message='Answer submitted successfully'
            )
        except (ExamNotFoundError, SubmissionValidationError) as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


class SessionProgressView(generics.GenericAPIView):
    """Get progress information for an exam session."""
    permission_classes = [IsStudent]
    serializer_class = ProgressResponseSerializer

    @extend_schema(
        summary='Get session progress',
        description='Get progress info including answered questions and time remaining.',
        parameters=[
            OpenApiParameter('token', str, location=OpenApiParameter.PATH, description='Session Token'),
        ],
        responses={200: ProgressResponseSerializer},
        tags=['Exam Session']
    )
    def get(self, request, token):
        try:
            session, token_obj = ExamSessionService.validate_token(token, request.user)
        except ValueError as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        progress = QuestionService.get_session_progress(session)
        return StandardResponse.success(data=progress, message='Progress retrieved successfully')


class SessionSubmitView(generics.GenericAPIView):
    """Submit exam session for grading using session token."""
    permission_classes = [IsStudent]
    serializer_class = SessionSubmitResponseSerializer

    @extend_schema(
        summary='Submit exam session',
        description='Submit the exam session for grading.',
        parameters=[
            OpenApiParameter('token', str, location=OpenApiParameter.PATH, description='Session Token'),
        ],
        responses={200: SessionSubmitResponseSerializer},
        tags=['Exam Session']
    )
    def post(self, request, token):
        try:
            session, token_obj = ExamSessionService.validate_token(token, request.user)
        except ValueError as e:
            return StandardResponse.error(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.grading.services import GradingService
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            grade_history = GradingService.grade_session(session, grading_method='manual')

            # Notify via WebSocket
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f'exam_session_{token}',
                        {
                            'type': 'session_completed',
                            'message': 'Exam submitted successfully',
                            'reason': 'submitted',
                            'grade_history_id': grade_history.id,
                        }
                    )
            except Exception:
                pass

            return StandardResponse.success(
                data={
                    'grade_history_id': grade_history.id,
                    'status': grade_history.status,
                    'total_score': float(grade_history.total_score),
                    'max_score': float(grade_history.max_score),
                    'percentage': float(grade_history.percentage),
                },
                message='Exam submitted and graded successfully'
            )
        except Exception as e:
            logger.exception(f'Error submitting session: {e}')
            return StandardResponse.server_error(message=str(e))
