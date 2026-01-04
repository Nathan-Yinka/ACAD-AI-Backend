from django.db import models
from apps.accounts.models import User
from .exam import Exam


class Submission(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GRADED', 'Graded'),
        ('FAILED', 'Failed'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        db_table = 'submissions'
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['exam', 'status']),
            models.Index(fields=['-submitted_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.student.email} - {self.exam.title} - {self.submitted_at}'

    def calculate_percentage(self):
        """Calculate the percentage score for this submission."""
        if self.max_score == 0:
            return 0.00
        return round((self.total_score / self.max_score) * 100, 2)

