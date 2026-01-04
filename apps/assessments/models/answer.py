from django.db import models
from .submission import Submission
from .question import Question


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'answers'
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        unique_together = [['submission', 'question']]
        indexes = [
            models.Index(fields=['submission', 'question']),
            models.Index(fields=['submission']),
        ]

    def __str__(self):
        return f'{self.submission} - {self.question}'

