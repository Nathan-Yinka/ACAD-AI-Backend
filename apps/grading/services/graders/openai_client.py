"""OpenAI LLM client for grading operations."""
import logging
import json
import os
from typing import Dict, Optional
from django.conf import settings
from apps.core.exceptions import GradingError

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI LLM client for making API calls with JSON response mode."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from settings/env.
        """
        self.api_key = api_key or self._get_api_key()
        if not self.api_key:
            raise GradingError('OpenAI API key not configured.')
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise GradingError('OpenAI package not installed. Install with: pip install openai')
    
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from settings or environment."""
        return (
            getattr(settings, 'OPENAI_API_KEY', '') or 
            os.getenv('OPENAI_API_KEY', '')
        )
    
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = 'gpt-4.1',
        temperature: float = 0.3,
        max_tokens: int = 200,
        json_response: bool = True
    ) -> Dict:
        """
        Complete a chat completion request with OpenAI.
        
        Args:
            system_prompt: System message content
            user_prompt: User message content
            model: Model to use (default: gpt-4.1)
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum tokens in response (default: 200)
            json_response: Whether to use JSON response format (default: True)
            
        Returns:
            Dictionary with 'content' (str) and 'usage' (dict) keys
            
        Raises:
            GradingError: If API call fails
        """
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            params = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
            
            # Add JSON response format if requested
            if json_response:
                params['response_format'] = {'type': 'json_object'}
            
            response = self.client.chat.completions.create(**params)
            
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            return {
                'content': content,
                'usage': usage
            }
            
        except Exception as e:
            logger.error(f'OpenAI API error: {str(e)}')
            raise GradingError(f'OpenAI API error: {str(e)}')
    
    def parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON response, handling markdown code blocks if present.
        
        Args:
            response_text: Raw response text from API
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            GradingError: If JSON parsing fails
        """
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise GradingError(f'Failed to parse JSON response: {str(e)}')

