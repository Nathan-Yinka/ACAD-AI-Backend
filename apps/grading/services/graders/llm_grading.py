"""LLM-based grading service implementation."""
import logging
import json
import re
from typing import Dict, Optional, List
from pathlib import Path
from django.conf import settings
from .base import BaseGradingService
from .openai_client import OpenAIClient
from apps.assessments.models import Submission
from apps.core.exceptions import GradingError

logger = logging.getLogger(__name__)


class LLMGradingService(BaseGradingService, OpenAIClient):
    """LLM-based grading service using OpenAI with JSON response mode."""
    
    def __init__(self):
        # Initialize OpenAI client (parent class)
        try:
            OpenAIClient.__init__(self)
        except GradingError:
            raise GradingError('OpenAI API key not configured.')
        
        self.max_retries = 3
        self.model = 'gpt-4.1'  # Use GPT-4.1 model
        self.system_prompt = 'You are an expert academic grader. Always respond with valid JSON only.'
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        try:
            prompt_file = Path(__file__).parent / 'llm_grading_prompt.txt'
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f'Failed to load prompt template: {e}. Using fallback prompt.')
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if file loading fails."""
        return """You are an expert grader evaluating a student's answer.

                Question: {question_text}
                Expected Answer/Key Points: {expected_answer}
                Student's Answer: {answer_text}
                Maximum Points: {max_points}

                Please provide:
                1. A score from 0 to {max_points} (as a decimal number)
                2. Brief feedback explaining the score

                Format your response as:
                SCORE: [number]
                FEEDBACK: [your feedback]"""
    
    def _create_grading_prompt(self, question_text: str, expected_answer: str, 
                               answer_text: str, max_points: int) -> str:
        """Create a prompt for LLM grading using the template."""
        max_points_minus_one = max_points - 1 if max_points > 1 else 0
        
        prompt = self.prompt_template.format(
            question_text=question_text,
            expected_answer=expected_answer,
            answer_text=answer_text,
            max_points=max_points,
            max_points_minus_one=max_points_minus_one
        )
        return prompt
    
    def _validate_llm_response(self, response_text: str, max_points: int) -> bool:
        """Validate that the LLM response is valid JSON with required fields."""
        if not response_text or not response_text.strip():
            return False
        
        # Try to parse as JSON using the client's parse method
        try:
            data = self.parse_json_response(response_text)
            
            # Validate required fields
            if not isinstance(data, dict):
                return False
            
            if 'score' not in data or 'feedback' not in data:
                return False
            
            # Validate score type and range
            score = data['score']
            if not isinstance(score, (int, float)):
                return False
            
            if score < 0 or score > max_points:
                return False
            
            # Validate feedback is a string
            if not isinstance(data['feedback'], str):
                return False
            
            return True
        except (GradingError, ValueError, TypeError, AttributeError) as e:
            logger.debug(f'JSON validation failed: {e}')
            return False
    
    def _parse_llm_response(self, response_text: str, max_points: int) -> Dict:
        """Parse LLM JSON response to extract score and feedback."""
        score = 0.0
        feedback = 'Grading completed.'
        
        try:
            # Use the client's parse_json_response method
            data = self.parse_json_response(response_text)
            
            # Extract score and feedback
            score = float(data.get('score', 0.0))
            score = max(0.0, min(score, float(max_points)))
            feedback = str(data.get('feedback', 'Grading completed.')).strip()
            
        except (GradingError, ValueError, TypeError, KeyError) as e:
            logger.warning(f'Failed to parse JSON response: {e}. Response: {response_text[:200]}')
            # Fallback: try to extract from text format (for backward compatibility)
            score_match = re.search(r'SCORE:\s*([\d.]+)', response_text, re.IGNORECASE)
            if score_match:
                try:
                    score = float(score_match.group(1))
                    score = max(0.0, min(score, float(max_points)))
                except ValueError:
                    score = 0.0
            
            feedback_match = re.search(r'FEEDBACK:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
            if feedback_match:
                feedback = feedback_match.group(1).strip()
        
        return {'score': round(score, 2), 'feedback': feedback or 'Grading completed.'}
    
    def _grade_with_openai(self, user_prompt: str) -> str:
        """Grade using OpenAI API via the complete method."""
        try:
            response = self.complete(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                json_response=True
            )
            return response['content']
        except Exception as e:
            raise GradingError(f'OpenAI API error: {str(e)}')
    
    def grade_answer(
        self, 
        answer_text: str, 
        expected_answer: str, 
        max_points: int,
        question_type: str = 'SHORT_ANSWER',
        options: Optional[List] = None,
        allow_multiple: bool = False,
        question_text: str = ''
    ) -> Dict:
        """Grade a single answer using LLM with validation and retry logic."""
        if not answer_text or not answer_text.strip():
            return {'score': 0.0, 'feedback': 'No answer provided.'}
        
        if question_type == 'MULTIPLE_CHOICE':
            return self._grade_multiple_choice(answer_text, expected_answer, max_points, allow_multiple)
        
        prompt = self._create_grading_prompt(question_text or 'N/A', expected_answer, answer_text, max_points)
        
        # Retry logic with validation
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Use OpenAI via the complete method
                response_text = self._grade_with_openai(prompt)
                
                # Validate response format
                if self._validate_llm_response(response_text, max_points):
                    return self._parse_llm_response(response_text, max_points)
                else:
                    logger.warning(
                        f'LLM response validation failed (attempt {attempt}/{self.max_retries}). '
                        f'Response: {response_text[:200]}'
                    )
                    if attempt < self.max_retries:
                        # Add instruction to retry with better JSON format
                        prompt = prompt + "\n\nIMPORTANT: Please ensure your response is valid JSON in this exact format:\n{\"score\": [number], \"feedback\": \"[text]\"}"
                        continue
                    else:
                        # Last attempt failed validation, try to parse anyway
                        logger.warning('Max retries reached. Attempting to parse invalid response.')
                        return self._parse_llm_response(response_text, max_points)
                        
            except Exception as e:
                last_error = e
                logger.warning(f'LLM grading attempt {attempt}/{self.max_retries} failed: {str(e)}')
                if attempt < self.max_retries:
                    continue
                else:
                    raise GradingError(f'LLM grading failed after {self.max_retries} attempts: {str(last_error)}')
        
        # Should not reach here, but just in case
        raise GradingError(f'LLM grading failed: {str(last_error)}')
    
    def grade_submission(self, submission: Submission) -> Dict:
        """Grade a complete submission using LLM."""
        logger.info(f'Grading submission {submission.id} using LLMGradingService (OpenAI)')
        answers_data = []
        total_score = 0.0
        
        answers = submission.answers.select_related('question').all()
        
        for answer in answers:
            question = answer.question
            
            try:
                grading_result = self.grade_answer(
                    answer.answer_text,
                    question.expected_answer,
                    question.points,
                    question_type=question.question_type,
                    options=question.options,
                    allow_multiple=question.allow_multiple,
                    question_text=question.question_text
                )
            except Exception as e:
                logger.error(f'LLM grading error for answer {answer.id}: {str(e)}')
                grading_result = {'score': 0.0, 'feedback': f'Grading error: {str(e)}'}
            
            answers_data.append({
                'answer_id': answer.id,
                'score': grading_result['score'],
                'feedback': grading_result.get('feedback', '')
            })
            total_score += grading_result['score']
        
        return {
            'answers': answers_data,
            'total_score': round(total_score, 2),
            'status': 'GRADED'
        }

