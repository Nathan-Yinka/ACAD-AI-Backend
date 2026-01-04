from django.db import models
from apps.accounts.models import User
from apps.assessments.models import Exam


class GradeHistory(models.Model):
    """Stores grading history for completed exam sessions."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grade_history')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grade_history')
    session_id = models.PositiveIntegerField(help_text='Reference to the exam session')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    total_score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    answers_data = models.JSONField(default=dict, help_text='Snapshot of answers with scores')
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    grading_method = models.CharField(max_length=50, default='auto', help_text='auto, manual, expired')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grade_history'
        verbose_name = 'Grade History'
        verbose_name_plural = 'Grade Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.student.email} - {self.exam.title} - {self.status}'

    def calculate_percentage(self):
        """Calculate the percentage score."""
        if self.max_score == 0:
            return 0.00
        return round((self.total_score / self.max_score) * 100, 2)

