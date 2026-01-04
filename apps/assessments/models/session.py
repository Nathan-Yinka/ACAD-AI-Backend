"""ExamSession model for tracking student exam attempts."""
from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from .exam import Exam


class ExamSession(models.Model):
    """Tracks student exam attempts with timer and answers."""
    
    SUBMISSION_TYPE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('AUTO_EXPIRED', 'Auto Expired'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_sessions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submission_type = models.CharField(max_length=15, choices=SUBMISSION_TYPE_CHOICES, null=True, blank=True)
    current_question_order = models.PositiveIntegerField(default=1, help_text='Current question being viewed')

    class Meta:
        db_table = 'exam_sessions'
        verbose_name = 'Exam Session'
        verbose_name_plural = 'Exam Sessions'
        ordering = ['-started_at']
        unique_together = [['student', 'exam']]
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['exam', 'is_completed']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['-started_at']),
            models.Index(fields=['is_completed', 'expires_at']),
        ]

    def __str__(self):
        return f'{self.student.email} - {self.exam.title} - {self.started_at}'

    def save(self, *args, **kwargs):
        """Set expires_at if not already set."""
        if not self.expires_at and self.exam:
            self.expires_at = timezone.now() + timedelta(minutes=self.exam.duration_minutes)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the exam session has expired."""
        return timezone.now() > self.expires_at

    def is_active(self):
        """Check if session is active (not expired, not completed)."""
        return not self.is_expired() and not self.is_completed

    def time_remaining_seconds(self):
        """Return the remaining time in seconds for this session."""
        if self.is_expired():
            return 0
        remaining = self.expires_at - timezone.now()
        return int(remaining.total_seconds())

    def mark_completed(self, submission_type='MANUAL'):
        """Mark this session as completed and set submission time."""
        self.is_completed = True
        self.submitted_at = timezone.now()
        self.submission_type = submission_type
        # Invalidate all tokens
        self.tokens.filter(is_valid=True).update(
            is_valid=False,
            invalidated_at=timezone.now()
        )
        self.save()

    def get_current_token(self):
        """Get the current valid token for this session."""
        return self.tokens.filter(is_valid=True).first()

    def create_new_token(self):
        """Create a new token, invalidating all previous ones."""
        from .session_token import SessionToken
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        # Invalidate and notify all existing valid tokens
        old_tokens = list(self.tokens.filter(is_valid=True).values_list('token', flat=True))
        self.tokens.filter(is_valid=True).update(
            is_valid=False,
            invalidated_at=timezone.now()
        )
        
        # Send expired event to all old token WebSocket connections
        channel_layer = get_channel_layer()
        if channel_layer:
            for old_token in old_tokens:
                try:
                    async_to_sync(channel_layer.group_send)(
                        f'exam_session_{old_token}',
                        {
                            'type': 'session_expired',
                            'message': 'A new session token has been issued. This token is no longer valid.',
                            'reason': 'token_expired',
                        }
                    )
                except Exception:
                    pass
        
        # Create new token
        new_token = SessionToken.objects.create(session=self)
        return new_token

    def get_answered_count(self):
        """Return the count of answered questions."""
        return self.student_answers.count()

    def get_total_questions(self):
        """Return total questions in the exam."""
        return self.exam.get_questions_count()
