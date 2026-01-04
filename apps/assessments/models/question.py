from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import json
from .exam import Exam


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('SHORT_ANSWER', 'Short Answer'),
        ('ESSAY', 'Essay'),
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='SHORT_ANSWER')
    expected_answer = models.TextField(
        help_text='Expected answer or answer key for grading. For multiple choice with allow_multiple=True, use JSON array like ["A", "B"]'
    )
    options = models.JSONField(
        default=list,
        blank=True,
        help_text='List of option objects for multiple choice questions. Format: [{"label": "A", "value": "Paris"}, {"label": "B", "value": "London"}]'
    )
    allow_multiple = models.BooleanField(
        default=False,
        help_text='Allow multiple answers to be selected (only for MULTIPLE_CHOICE questions)'
    )
    points = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    order = models.PositiveIntegerField(default=1, help_text='Order of the question within the exam')
    
    def clean(self):
        """Validate question data based on question type."""
        super().clean()
        if self.question_type == 'MULTIPLE_CHOICE':
            if not self.options or len(self.options) < 2:
                raise ValidationError({'options': 'Multiple choice questions must have at least 2 options.'})
            if not isinstance(self.options, list):
                raise ValidationError({'options': 'Options must be a list.'})
            
            option_values = []
            for idx, option in enumerate(self.options):
                if not isinstance(option, dict):
                    raise ValidationError({'options': f'Option {idx} must be an object with "label" and "value" keys.'})
                if 'label' not in option or 'value' not in option:
                    raise ValidationError({'options': f'Option {idx} must have both "label" and "value" keys.'})
                option_values.append(option['value'])
            
            if self.expected_answer:
                try:
                    expected_answers = json.loads(self.expected_answer)
                    if not isinstance(expected_answers, list):
                        expected_answers = [self.expected_answer]
                except (json.JSONDecodeError, TypeError):
                    expected_answers = [self.expected_answer]
                
                for expected in expected_answers:
                    if expected not in option_values:
                        raise ValidationError({
                            'expected_answer': f'Expected answer "{expected}" must be one of the option values: {", ".join(option_values)}'
                        })
        
        if self.allow_multiple and self.question_type != 'MULTIPLE_CHOICE':
            raise ValidationError({'allow_multiple': 'allow_multiple can only be True for MULTIPLE_CHOICE questions.'})
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_option_values(self):
        """Return list of valid option values for multiple choice questions."""
        if self.question_type == 'MULTIPLE_CHOICE' and self.options:
            return [opt['value'] for opt in self.options]
        return []
    
    def validate_answer(self, answer_text: str) -> bool:
        """Validate answer text based on question type and options."""
        if self.question_type == 'MULTIPLE_CHOICE':
            option_values = self.get_option_values()
            if not option_values:
                return False
            
            try:
                answers = json.loads(answer_text)
                if not isinstance(answers, list):
                    answers = [answer_text]
            except (json.JSONDecodeError, TypeError):
                answers = [answer_text]
            
            for answer in answers:
                if answer not in option_values:
                    return False
            
            if not self.allow_multiple and len(answers) > 1:
                return False
            
            return True
        return True

    class Meta:
        db_table = 'questions'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['exam', 'order']
        unique_together = [['exam', 'order']]
        indexes = [
            models.Index(fields=['exam', 'order']),
            models.Index(fields=['question_type']),
        ]

    def __str__(self):
        return f'{self.exam.title} - Question {self.order}'

