"""Service for managing exam sessions."""
import logging
from typing import Optional, Tuple
from django.utils import timezone
from apps.assessments.models import Exam, ExamSession, SessionToken
from apps.core.exceptions import ExamNotFoundError

logger = logging.getLogger(__name__)


class ExamSessionService:
    @staticmethod
    def get_session_by_token(token: str) -> Tuple[ExamSession, SessionToken]:
        """Get exam session by token. Returns (session, token_obj)."""
        try:
            token_obj = SessionToken.objects.select_related(
                'session', 'session__exam', 'session__student'
            ).get(token=token)
            return token_obj.session, token_obj
        except SessionToken.DoesNotExist:
            raise ValueError('Invalid session token.')

    @staticmethod
    def get_active_session(student, exam_id: int) -> Optional[ExamSession]:
        """Get exam session for a student and exam if exists."""
        try:
            return ExamSession.objects.select_related('exam').get(
                student=student,
                exam_id=exam_id
            )
        except ExamSession.DoesNotExist:
            return None

    @staticmethod
    def get_active_session_info(student, exam_id: int) -> Optional[dict]:
        """Get active session info for exam listing (without token)."""
        session = ExamSessionService.get_active_session(student, exam_id)
        if session and session.is_active():
            return {
                'session_id': session.id,
                'time_remaining_seconds': session.time_remaining_seconds(),
                'started_at': session.started_at.isoformat(),
                'expires_at': session.expires_at.isoformat(),
                'answered_count': session.get_answered_count(),
                'total_questions': session.get_total_questions(),
            }
        return None

    @staticmethod
    def get_grade_info(student, exam_id: int) -> Optional[dict]:
        """Get latest grade info for a student and exam."""
        from apps.grading.models import GradeHistory
        try:
            grade = GradeHistory.objects.filter(
                student=student,
                exam_id=exam_id,
                status='COMPLETED'
            ).order_by('-created_at').first()
            
            if grade:
                return {
                    'grade_id': grade.id,
                    'status': grade.status,
                    'total_score': float(grade.total_score),
                    'max_score': float(grade.max_score),
                    'percentage': float(grade.percentage),
                    'graded_at': grade.graded_at.isoformat() if grade.graded_at else None,
                    'submitted_at': grade.submitted_at.isoformat() if grade.submitted_at else None,
                }
        except Exception as e:
            logger.warning(f'Error fetching grade info for exam {exam_id}: {e}')
        return None

    @staticmethod
    def start_or_continue_session(student, exam_id: int) -> Tuple[ExamSession, SessionToken, str]:
        """Start new session or continue existing one. Returns (session, token, action)."""
        try:
            exam = Exam.objects.get(id=exam_id, is_active=True)
        except Exam.DoesNotExist:
            raise ExamNotFoundError('Exam not found or is not active.')
        
        session = ExamSessionService.get_active_session(student, exam_id)
        
        if session:
            if session.is_completed:
                raise ValueError('You have already completed this exam.')
            
            # Continue - create new token (invalidates old ones)
            new_token = session.create_new_token()
            logger.info(f'Session {session.id} continued with new token for exam {exam_id}')
            return session, new_token, 'continued'
        else:
            # Start new session
            session = ExamSession.objects.create(student=student, exam=exam)
            new_token = session.create_new_token()
            
            # Schedule auto-grade task at exact expiry time
            ExamSessionService._schedule_expiry_task(session)
            
            logger.info(f'New session {session.id} created for exam {exam_id} by {student.email}')
            return session, new_token, 'started'

    @staticmethod
    def _schedule_expiry_task(session: ExamSession):
        """Schedule a Celery task to run at exact session expiry time."""
        try:
            from django.conf import settings
            # Skip scheduling in test mode or when Celery is not configured
            if getattr(settings, 'TESTING', False):
                logger.info(f'Skipping task scheduling in test mode for session {session.id}')
                return
            
            from apps.grading.tasks import schedule_session_expiry
            schedule_session_expiry.apply_async(
                args=[session.id],
                eta=session.expires_at
            )
            logger.info(f'Scheduled expiry task for session {session.id} at {session.expires_at}')
        except Exception as e:
            logger.warning(f'Failed to schedule expiry task for session {session.id}: {e}')

    @staticmethod
    def validate_token(token: str, student) -> Tuple[ExamSession, SessionToken]:
        """Validate token belongs to student and is valid."""
        session, token_obj = ExamSessionService.get_session_by_token(token)
        
        if session.student_id != student.id:
            raise ValueError('Session does not belong to this user.')
        
        if not token_obj.is_valid:
            raise ValueError('Session token has expired.')
        
        if session.is_completed:
            raise ValueError('This exam session has already been completed.')
        
        if session.is_expired():
            raise ValueError('This exam session has expired.')
        
        return session, token_obj

    @staticmethod
    def check_token_validity(token: str) -> Tuple[bool, Optional[str]]:
        """Check if token is valid. Returns (is_valid, reason)."""
        try:
            token_obj = SessionToken.objects.select_related('session').get(token=token)
        except SessionToken.DoesNotExist:
            return False, 'invalid_token'
        
        if not token_obj.is_valid:
            return False, 'token_expired'
        
        if token_obj.session.is_completed:
            return False, 'session_completed'
        
        if token_obj.session.is_expired():
            return False, 'session_timeout'
        
        return True, None

    @staticmethod
    def validate_session_for_view(student, exam_id: int) -> Tuple[Optional[ExamSession], bool]:
        """Validate session for viewing exam questions."""
        session = ExamSessionService.get_active_session(student, exam_id)
        if session and session.is_active():
            return session, True
        return None, False

    @staticmethod
    def mark_session_completed(session: ExamSession, submission_type: str = 'MANUAL'):
        """Mark an exam session as completed."""
        session.mark_completed(submission_type)
        logger.info(f'Exam session {session.id} marked as completed ({submission_type})')
