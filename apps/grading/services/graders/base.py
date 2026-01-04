"""Base class for grading services."""
import json
from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class BaseGradingService(ABC):
    """Abstract base class for grading services."""
    
    def _grade_multiple_choice(
        self, 
        answer_text: str, 
        expected_answer: str, 
        max_points: int,
        allow_multiple: bool
    ) -> Dict:
        """Grade multiple choice questions (binary scoring or proportional for multi-select)."""
        try:
            student_answers = json.loads(answer_text) if allow_multiple else [answer_text]
            if not isinstance(student_answers, list):
                student_answers = [answer_text]
        except (json.JSONDecodeError, TypeError):
            student_answers = [answer_text]
        
        try:
            expected_answers = json.loads(expected_answer) if allow_multiple else [expected_answer]
            if not isinstance(expected_answers, list):
                expected_answers = [expected_answer]
        except (json.JSONDecodeError, TypeError):
            expected_answers = [expected_answer]
        
        student_set = set(student_answers)
        expected_set = set(expected_answers)
        
        if allow_multiple:
            correct_selected = len(student_set.intersection(expected_set))
            incorrect_selected = len(student_set - expected_set)
            total_expected = len(expected_set)
            
            if total_expected == 0:
                return {'score': 0.0, 'feedback': 'No correct answer defined.'}
            
            correct_score = (correct_selected / total_expected) * max_points
            penalty = (incorrect_selected / total_expected) * max_points if incorrect_selected > 0 else 0
            final_score = max(0.0, correct_score - penalty)
            final_score = round(final_score, 2)
            
            if final_score == max_points:
                feedback = 'All correct answers selected.'
            elif correct_selected > 0:
                feedback = f'{correct_selected} out of {total_expected} correct answers selected.'
            else:
                feedback = 'Incorrect answer(s) selected.'
        else:
            if student_set == expected_set:
                final_score = float(max_points)
                feedback = 'Correct answer selected.'
            else:
                final_score = 0.0
                feedback = 'Incorrect answer selected.'
        
        return {'score': final_score, 'feedback': feedback}
    
    @abstractmethod
    def grade_answer(
        self, 
        answer_text: str, 
        expected_answer: str, 
        max_points: int,
        question_type: str = 'SHORT_ANSWER',
        options: Optional[List] = None,
        allow_multiple: bool = False
    ) -> Dict:
        """
        Grade a single answer.
        
        Args:
            answer_text: Student's answer text (JSON string for multi-choice)
            expected_answer: Expected/correct answer (JSON string for multi-choice)
            max_points: Maximum points for this question
            question_type: Type of question (SHORT_ANSWER, ESSAY, MULTIPLE_CHOICE)
            options: List of option objects for multiple choice questions
            allow_multiple: Whether multiple answers are allowed (for MCQ)
            
        Returns:
            Dictionary with 'score' (float) and 'feedback' (str)
        """
        pass
    
    @abstractmethod
    def grade_submission(self, submission) -> Dict:
        """
        Grade an entire submission with multiple answers.
        
        Args:
            submission: Submission model instance
            
        Returns:
            Dictionary with:
                - 'status': str (PENDING, GRADED, FAILED)
                - 'total_score': float
                - 'answers': List of dicts with 'answer_id', 'score', 'feedback'
        """
        pass
