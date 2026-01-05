"""Celery tasks for session management and auto-grading."""
import logging
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(name='grading.schedule_session_expiry')
def schedule_session_expiry(session_id: int):
    """
    Scheduled task that runs at exact session expiry time.
    Called when a session is created with ETA set to expires_at.
    """
    from apps.assessments.models import ExamSession
    
    try:
        session = ExamSession.objects.select_related('exam', 'student').get(id=session_id)
    except ExamSession.DoesNotExist:
        logger.warning(f'Session {session_id} not found')
        return
    
    # Already completed (manually submitted) - nothing to do
    if session.is_completed:
        logger.info(f'Session {session_id} already completed, skipping expiry task')
        return
    
    # Double-check it's actually expired
    if not session.is_expired():
        logger.warning(f'Session {session_id} not yet expired, rescheduling')
        # This shouldn't happen, but reschedule just in case
        remaining = (session.expires_at - timezone.now()).total_seconds()
        if remaining > 0:
            schedule_session_expiry.apply_async(args=[session_id], countdown=remaining)
        return
    
    # Get all valid tokens before grading
    valid_tokens = list(session.tokens.filter(is_valid=True).values_list('token', flat=True))
    
    # Grade the session
    grade_expired_session_now(session, valid_tokens)


def grade_expired_session_now(session, tokens: list):
    """Grade an expired session in background and notify via WebSocket immediately."""
    # Send WebSocket event immediately without waiting for grading
    channel_layer = get_channel_layer()
    if channel_layer:
        for token in tokens:
            try:
                async_to_sync(channel_layer.group_send)(
                    f'exam_session_{token}',
                    {
                        'type': 'session_completed',
                        'message': 'Exam time has ended. Your answers have been submitted. Grading in progress.',
                        'reason': 'timeout',
                    }
                )
            except Exception:
                pass
    
    # Grade in background (async)
    try:
        from apps.grading.services import GradingService
        grade_history = GradingService.grade_session(session, grading_method='timeout')
        logger.info(f'Graded expired session {session.id}, score: {grade_history.total_score}/{grade_history.max_score}')
        return grade_history.id
    except Exception as e:
        logger.error(f'Failed to grade expired session {session.id}: {e}', exc_info=True)
        raise


@shared_task(name='grading.check_expired_sessions')
def check_expired_sessions():
    """
    Fallback periodic task to catch any missed expired sessions.
    Runs every minute as a safety net.
    """
    from apps.assessments.models import ExamSession
    print("Checking expired sessions")
    print("Checking expired sessions")
    print("Checking expired sessions")
    print("Checking expired sessions")
    
    expired_sessions = ExamSession.objects.filter(
        is_completed=False,
        expires_at__lte=timezone.now()
    ).select_related('exam', 'student')
    
    count = 0
    for session in expired_sessions:
        valid_tokens = list(session.tokens.filter(is_valid=True).values_list('token', flat=True))
        grade_expired_session_now(session, valid_tokens)
        count += 1
    
    if count > 0:
        logger.info(f'Fallback task: graded {count} expired sessions')
    
    return count


@shared_task(name='grading.grade_expired_session')
def grade_expired_session(session_id: int, tokens: list = None):
    """Grade an expired session by ID (for manual triggering or delayed calls)."""
    from apps.assessments.models import ExamSession
    
    try:
        session = ExamSession.objects.select_related('exam', 'student').get(id=session_id)
    except ExamSession.DoesNotExist:
        logger.warning(f'Session {session_id} not found for grading')
        return
    
    if session.is_completed:
        logger.info(f'Session {session_id} already completed, skipping')
        return
    
    if tokens is None:
        tokens = list(session.tokens.filter(is_valid=True).values_list('token', flat=True))
    
    return grade_expired_session_now(session, tokens)


def grade_submitted_session_now(session, token: str):
    """Grade a submitted session in background and notify via WebSocket immediately."""
    # Send WebSocket event immediately without waiting for grading
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f'exam_session_{token}',
                {
                    'type': 'session_completed',
                    'message': 'Exam submitted successfully. Grading in progress.',
                    'reason': 'submitted',
                }
            )
        except Exception:
            pass
    
    # Grade in background (async)
    try:
        from apps.grading.services import GradingService
        grade_history = GradingService.grade_session(session, grading_method='manual')
        logger.info(f'Graded submitted session {session.id}, score: {grade_history.total_score}/{grade_history.max_score}')
        return grade_history.id
    except Exception as e:
        logger.error(f'Failed to grade submitted session {session.id}: {e}', exc_info=True)
        raise


@shared_task(name='grading.grade_submitted_session')
def grade_submitted_session(session_id: int, token: str):
    """Grade a submitted session by ID (for background processing)."""
    from apps.assessments.models import ExamSession
    
    try:
        session = ExamSession.objects.select_related('exam', 'student').get(id=session_id)
    except ExamSession.DoesNotExist:
        logger.warning(f'Session {session_id} not found for grading')
        return
    
    return grade_submitted_session_now(session, token)
