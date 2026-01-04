from django.db import models
from django.core.validators import MinValueValidator


class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Duration of the exam in minutes'
    )
    course = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'exams'
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_questions_count(self):
        """Return the total number of questions in this exam."""
        return self.questions.count()

    def get_max_score(self):
        """Return the maximum possible score for this exam."""
        return self.questions.aggregate(
            total=models.Sum('points')
        )['total'] or 0

    def has_active_sessions(self):
        """Check if exam has any active (not completed) sessions."""
        from django.utils import timezone
        return self.sessions.filter(is_completed=False, expires_at__gt=timezone.now()).exists()

    def has_submissions(self):
        """Check if exam has any submissions."""
        return self.submissions.exists()

