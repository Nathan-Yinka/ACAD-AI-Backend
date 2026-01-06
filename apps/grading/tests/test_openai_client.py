"""Tests for OpenAI client."""
import json
import sys
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.grading.services.graders.openai_client import OpenAIClient
from apps.core.exceptions import GradingError


class OpenAIClientTests(TestCase):
    """Tests for OpenAIClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_api_key = 'test-api-key-12345'
        self.client = None

    @patch('openai.OpenAI')
    def test_init_with_api_key(self, mock_openai_class):
        """Test initialization with provided API key."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        
        client = OpenAIClient(api_key=self.test_api_key)
        
        self.assertEqual(client.api_key, self.test_api_key)
        mock_openai_class.assert_called_once_with(api_key=self.test_api_key)

    @patch('openai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-api-key'}, clear=False)
    @patch('django.conf.settings.OPENAI_API_KEY', 'env-api-key')
    def test_init_without_api_key_uses_env(self, mock_openai_class):
        """Test initialization without API key uses environment variable."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        
        # Temporarily override settings
        from django.conf import settings
        original_key = getattr(settings, 'OPENAI_API_KEY', None)
        settings.OPENAI_API_KEY = 'env-api-key'
        
        try:
            client = OpenAIClient()
            self.assertEqual(client.api_key, 'env-api-key')
            mock_openai_class.assert_called_once_with(api_key='env-api-key')
        finally:
            if original_key is not None:
                settings.OPENAI_API_KEY = original_key
            elif hasattr(settings, 'OPENAI_API_KEY'):
                delattr(settings, 'OPENAI_API_KEY')

    @patch('openai.OpenAI')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_api_key_raises_error(self, mock_openai_class):
        """Test initialization without API key raises error when not in env."""
        # Temporarily override settings
        from django.conf import settings
        original_key = getattr(settings, 'OPENAI_API_KEY', None)
        if hasattr(settings, 'OPENAI_API_KEY'):
            settings.OPENAI_API_KEY = ''
        
        try:
            with self.assertRaises(GradingError) as context:
                OpenAIClient()
            self.assertIn('OpenAI API key not configured', str(context.exception))
        finally:
            if original_key is not None:
                settings.OPENAI_API_KEY = original_key
            elif hasattr(settings, 'OPENAI_API_KEY'):
                delattr(settings, 'OPENAI_API_KEY')


    @patch('openai.OpenAI')
    def test_complete_with_json_response(self, mock_openai_class):
        """Test complete method with JSON response mode."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 8.5, "feedback": "Good answer"}'
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80
        
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key=self.test_api_key)
        result = client.complete(
            system_prompt='You are a grader',
            user_prompt='Grade this answer',
            model='gpt-4.1',
            json_response=True
        )
        
        # Verify result
        self.assertEqual(result['content'], '{"score": 8.5, "feedback": "Good answer"}')
        self.assertEqual(result['usage']['prompt_tokens'], 50)
        self.assertEqual(result['usage']['completion_tokens'], 30)
        self.assertEqual(result['usage']['total_tokens'], 80)
        
        # Verify API call
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args = mock_client_instance.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], 'gpt-4.1')
        self.assertEqual(call_args['response_format'], {'type': 'json_object'})
        self.assertEqual(call_args['temperature'], 0.3)
        self.assertEqual(call_args['max_tokens'], 200)

    @patch('openai.OpenAI')
    def test_complete_without_json_response(self, mock_openai_class):
        """Test complete method without JSON response mode."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Some text response'
        mock_response.usage.prompt_tokens = 40
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 60
        
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key=self.test_api_key)
        result = client.complete(
            system_prompt='You are a grader',
            user_prompt='Grade this answer',
            json_response=False
        )
        
        # Verify result
        self.assertEqual(result['content'], 'Some text response')
        
        # Verify API call doesn't include response_format
        call_args = mock_client_instance.chat.completions.create.call_args[1]
        self.assertNotIn('response_format', call_args)

    @patch('openai.OpenAI')
    def test_complete_custom_parameters(self, mock_openai_class):
        """Test complete method with custom parameters."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = 'Response'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        mock_client_instance.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient(api_key=self.test_api_key)
        client.complete(
            system_prompt='System',
            user_prompt='User',
            model='gpt-4.1',
            temperature=0.7,
            max_tokens=500
        )
        
        # Verify custom parameters
        call_args = mock_client_instance.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], 'gpt-4.1')
        self.assertEqual(call_args['temperature'], 0.7)
        self.assertEqual(call_args['max_tokens'], 500)

    @patch('openai.OpenAI')
    def test_complete_api_error(self, mock_openai_class):
        """Test complete method handles API errors."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception('API Error')
        
        client = OpenAIClient(api_key=self.test_api_key)
        
        with self.assertRaises(GradingError) as context:
            client.complete(
                system_prompt='System',
                user_prompt='User'
            )
        self.assertIn('OpenAI API error', str(context.exception))

    def test_parse_json_response_valid_json(self):
        """Test parse_json_response with valid JSON."""
        client = OpenAIClient.__new__(OpenAIClient)  # Create instance without __init__
        
        response_text = '{"score": 8.5, "feedback": "Good answer"}'
        result = client.parse_json_response(response_text)
        
        self.assertEqual(result['score'], 8.5)
        self.assertEqual(result['feedback'], 'Good answer')

    def test_parse_json_response_with_markdown_code_block(self):
        """Test parse_json_response handles markdown code blocks."""
        client = OpenAIClient.__new__(OpenAIClient)
        
        response_text = '```json\n{"score": 7.0, "feedback": "Partial credit"}\n```'
        result = client.parse_json_response(response_text)
        
        self.assertEqual(result['score'], 7.0)
        self.assertEqual(result['feedback'], 'Partial credit')

    def test_parse_json_response_with_json_code_block(self):
        """Test parse_json_response handles ```json code blocks."""
        client = OpenAIClient.__new__(OpenAIClient)
        
        response_text = '```json\n{"score": 9.0, "feedback": "Excellent"}\n```'
        result = client.parse_json_response(response_text)
        
        self.assertEqual(result['score'], 9.0)
        self.assertEqual(result['feedback'], 'Excellent')

    def test_parse_json_response_invalid_json(self):
        """Test parse_json_response raises error for invalid JSON."""
        client = OpenAIClient.__new__(OpenAIClient)
        
        response_text = 'Not valid JSON'
        
        with self.assertRaises(GradingError) as context:
            client.parse_json_response(response_text)
        self.assertIn('Failed to parse JSON response', str(context.exception))

    def test_parse_json_response_empty_string(self):
        """Test parse_json_response handles empty string."""
        client = OpenAIClient.__new__(OpenAIClient)
        
        response_text = ''
        
        with self.assertRaises(GradingError):
            client.parse_json_response(response_text)

    def test_parse_json_response_complex_json(self):
        """Test parse_json_response with complex JSON structure."""
        client = OpenAIClient.__new__(OpenAIClient)
        
        response_text = '{"score": 10.0, "feedback": "Perfect answer with detailed explanation"}'
        result = client.parse_json_response(response_text)
        
        self.assertEqual(result['score'], 10.0)
        self.assertEqual(result['feedback'], 'Perfect answer with detailed explanation')
        self.assertGreater(len(result['feedback']), 0)

