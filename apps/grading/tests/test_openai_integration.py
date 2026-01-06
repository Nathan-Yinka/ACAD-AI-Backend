"""Integration tests for LLM grading service - tests actual API calls with real data."""
import os
from django.test import TestCase
from django.conf import settings
from apps.grading.services.graders.llm_grading import LLMGradingService
from apps.core.exceptions import GradingError


class LLMGradingIntegrationTests(TestCase):
    """Integration tests for LLMGradingService that make real OpenAI API calls."""
    
    @classmethod
    def setUpClass(cls):
        """Check if we have an API key before running tests."""
        super().setUpClass()
        cls.api_key = (
            getattr(settings, 'OPENAI_API_KEY', '') or 
            os.getenv('OPENAI_API_KEY', '')
        )
        cls.skip_all = not cls.api_key
    
    def setUp(self):
        """Skip tests if no API key is available."""
        if self.skip_all:
            self.skipTest("OpenAI API key not configured. Set OPENAI_API_KEY environment variable to run integration tests.")
    
    def test_grade_correct_answer_real_api(self):
        """Test grading a correct answer with real OpenAI API call."""
        try:
            service = LLMGradingService()
        except GradingError as e:
            self.skipTest(f"Failed to initialize LLM service: {e}")
        
        result = service.grade_answer(
            answer_text='Paris',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify result structure
        self.assertIn('score', result)
        self.assertIn('feedback', result)
        self.assertIsInstance(result['score'], (int, float))
        self.assertIsInstance(result['feedback'], str)
        
        # Verify score is in valid range
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 10)
        
        # For a correct answer, score should be high
        self.assertGreater(result['score'], 8.0, f"Expected high score for correct answer, got {result['score']}")
        self.assertIn('Paris', result['feedback'] or '')
    
    def test_grade_wrong_answer_real_api(self):
        """Test grading a wrong answer with real OpenAI API call."""
        try:
            service = LLMGradingService()
        except GradingError as e:
            self.skipTest(f"Failed to initialize LLM service: {e}")
        
        result = service.grade_answer(
            answer_text='5',
            expected_answer='4',
            max_points=5,
            question_type='SHORT_ANSWER',
            question_text='What is 2 + 2?'
        )
        
        # Verify result structure
        self.assertIn('score', result)
        self.assertIn('feedback', result)
        
        # Verify score is in valid range
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 5)
        
        # For a wrong answer, score should be low
        self.assertLess(result['score'], 2.0, f"Expected low score for wrong answer, got {result['score']}")
    
    def test_grade_partial_answer_real_api(self):
        """Test grading a partial answer with real OpenAI API call."""
        try:
            service = LLMGradingService()
        except GradingError as e:
            self.skipTest(f"Failed to initialize LLM service: {e}")
        
        result = service.grade_answer(
            answer_text='Photosynthesis is when plants use sunlight to make food.',
            expected_answer='Photosynthesis is the process by which plants convert light energy into chemical energy, producing glucose and oxygen from carbon dioxide and water.',
            max_points=20,
            question_type='ESSAY',
            question_text='Explain the concept of photosynthesis.'
        )
        
        # Verify result structure
        self.assertIn('score', result)
        self.assertIn('feedback', result)
        
        # Verify score is in valid range
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 20)
        
        # For a partial answer, score should be between 0 and max_points
        self.assertGreater(result['score'], 0, "Expected some points for partial answer")
        self.assertLess(result['score'], 20, "Expected less than full points for partial answer")
    
    def test_grade_empty_answer_real_api(self):
        """Test grading an empty answer returns zero without API call."""
        try:
            service = LLMGradingService()
        except GradingError as e:
            self.skipTest(f"Failed to initialize LLM service: {e}")
        
        result = service.grade_answer(
            answer_text='',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Empty answer should return zero without API call
        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['feedback'], 'No answer provided.')
    
    def test_parse_json_response_with_markdown(self):
        """Test parsing JSON response that includes markdown code blocks."""
        try:
            service = LLMGradingService()
        except GradingError as e:
            self.skipTest(f"Failed to initialize LLM service: {e}")
        
        # Test with markdown-wrapped JSON (using the parse_json_response method from parent)
        test_cases = [
            '```json\n{"score": 8.5, "feedback": "Good answer"}\n```',
            '```\n{"score": 7.0, "feedback": "Partial credit"}\n```',
            '{"score": 10.0, "feedback": "Perfect answer"}',
        ]
        
        for test_json in test_cases:
            parsed = service.parse_json_response(test_json)
            self.assertIsInstance(parsed, dict)
            self.assertIn('score', parsed)
            self.assertIn('feedback', parsed)

