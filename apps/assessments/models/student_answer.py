from django.db import models
from .session import ExamSession
from .question import Question


class StudentAnswer(models.Model):
    """Tracks individual answers during an active exam session."""
    
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    answer_text = models.TextField()
    answered_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_answers'
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
        unique_together = [['session', 'question']]
        indexes = [
            models.Index(fields=['session', 'question']),
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f'{self.session} - Q{self.question.order}'

