"""Model for tracking session tokens."""
import secrets
from django.db import models
from django.utils import timezone


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


class SessionToken(models.Model):
    """Tracks all tokens issued for an exam session."""
    
    session = models.ForeignKey(
        'ExamSession',
        on_delete=models.CASCADE,
        related_name='tokens'
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'session_tokens'
        verbose_name = 'Session Token'
        verbose_name_plural = 'Session Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['session', 'is_valid']),
        ]

    def __str__(self):
        status = 'valid' if self.is_valid else 'expired'
        return f'{self.session_id} - {self.token[:8]}... ({status})'

    def save(self, *args, **kwargs):
        """Generate token if not set."""
        if not self.token:
            self.token = generate_token()
        super().save(*args, **kwargs)

    def invalidate(self):
        """Mark token as invalid."""
        self.is_valid = False
        self.invalidated_at = timezone.now()
        self.save(update_fields=['is_valid', 'invalidated_at'])

