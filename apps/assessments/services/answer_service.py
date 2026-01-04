import json
import logging
from apps.assessments.models import Question
from apps.core.exceptions import SubmissionValidationError

logger = logging.getLogger(__name__)


class AnswerService:
    @staticmethod
    def normalize_answer(question: Question, answer_text: str) -> str:
        """Normalize answer text based on question type (MCQ as JSON array, others as plain text)."""
        if question.question_type == 'MULTIPLE_CHOICE':
            try:
                answers = json.loads(answer_text)
                if not isinstance(answers, list):
                    answers = [answer_text]
            except (json.JSONDecodeError, TypeError):
                answers = [answer_text]
            
            option_values = question.get_option_values()
            for answer in answers:
                if answer not in option_values:
                    option_labels = [f"{opt['label']}: {opt['value']}" for opt in question.options]
                    raise SubmissionValidationError(
                        f'Invalid answer "{answer}" for question {question.id}. '
                        f'Answer must be one of: {", ".join(option_labels)}'
                    )
            
            if not question.allow_multiple and len(answers) > 1:
                raise SubmissionValidationError(
                    f'Question {question.id} only allows a single answer.'
                )
            
            if question.allow_multiple and len(answers) > 1:
                return json.dumps(answers)
            else:
                return answers[0] if answers else answer_text
        
        return answer_text
    
    @staticmethod
    def validate_answer(question: Question, answer_text: str) -> bool:
        """Validate answer text against question type and options."""
        return question.validate_answer(answer_text)

