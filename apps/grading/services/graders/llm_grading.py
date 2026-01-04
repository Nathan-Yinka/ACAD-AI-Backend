"""LLM-based grading service implementation."""
import logging
import os
from typing import Dict, Optional, List
from django.conf import settings
from .base import BaseGradingService
from apps.assessments.models import Submission
from apps.core.exceptions import GradingError

logger = logging.getLogger(__name__)


class LLMGradingService(BaseGradingService):
    """LLM-based grading service supporting OpenAI and Anthropic."""
    
    def __init__(self):
        self.provider = self._get_provider()
        self.api_key = self._get_api_key()
        
        if not self.api_key:
            raise GradingError('LLM API key not configured.')
    
    def _get_provider(self) -> str:
        """Get the LLM provider from settings."""
        return getattr(settings, 'LLM_PROVIDER', 'openai').lower()
    
    def _get_api_key(self) -> Optional[str]:
        """Get the API key for the configured provider."""
        if self.provider == 'openai':
            return getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')
        elif self.provider == 'anthropic':
            return getattr(settings, 'ANTHROPIC_API_KEY', '') or os.getenv('ANTHROPIC_API_KEY', '')
        return None
    
    def _create_grading_prompt(self, question_text: str, expected_answer: str, 
                               answer_text: str, max_points: int) -> str:
        """Create a prompt for LLM grading."""
        return f"""You are an expert grader evaluating a student's answer.

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
    
    def _parse_llm_response(self, response_text: str, max_points: int) -> Dict:
        """Parse LLM response to extract score and feedback."""
        score = 0.0
        feedback = 'Grading completed.'
        
        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('SCORE:'):
                try:
                    score_str = line.replace('SCORE:', '').strip()
                    score = float(score_str)
                    score = max(0.0, min(score, float(max_points)))
                except ValueError:
                    score = 0.0
            elif line.startswith('FEEDBACK:'):
                feedback = line.replace('FEEDBACK:', '').strip()
        
        return {'score': round(score, 2), 'feedback': feedback or 'Grading completed.'}
    
    def _grade_with_openai(self, prompt: str) -> str:
        """Grade using OpenAI API."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'You are an expert academic grader.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            raise GradingError(f'OpenAI API error: {str(e)}')
    
    def _grade_with_anthropic(self, prompt: str) -> str:
        """Grade using Anthropic API."""
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model='claude-3-haiku-20240307',
                max_tokens=200,
                temperature=0.3,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise GradingError(f'Anthropic API error: {str(e)}')
    
    def grade_answer(
        self, 
        answer_text: str, 
        expected_answer: str, 
        max_points: int,
        question_type: str = 'SHORT_ANSWER',
        options: Optional[List] = None,
        allow_multiple: bool = False
    ) -> Dict:
        """Grade a single answer using LLM (except MCQ which uses base class method)."""
        if not answer_text or not answer_text.strip():
            return {'score': 0.0, 'feedback': 'No answer provided.'}
        
        if question_type == 'MULTIPLE_CHOICE':
            return self._grade_multiple_choice(answer_text, expected_answer, max_points, allow_multiple)
        
        prompt = self._create_grading_prompt('', expected_answer, answer_text, max_points)
        
        try:
            if self.provider == 'openai':
                response_text = self._grade_with_openai(prompt)
            elif self.provider == 'anthropic':
                response_text = self._grade_with_anthropic(prompt)
            else:
                raise GradingError(f'Unsupported LLM provider: {self.provider}')
            
            return self._parse_llm_response(response_text, max_points)
        except Exception as e:
            raise GradingError(f'LLM grading failed: {str(e)}')
    
    def grade_submission(self, submission: Submission) -> Dict:
        """Grade a complete submission using LLM."""
        logger.info(f'Grading submission {submission.id} using LLMGradingService ({self.provider})')
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
                    allow_multiple=question.allow_multiple
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

