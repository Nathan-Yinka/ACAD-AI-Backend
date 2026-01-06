"""Tests for LLM grading service with actual question and answer scenarios."""
import json
from django.test import TestCase
from unittest.mock import patch, MagicMock, Mock
from apps.core.test_utils import create_test_user
from apps.assessments.models import Exam, Question, ExamSession, StudentAnswer, Submission, Answer
from apps.grading.services.graders.llm_grading import LLMGradingService
from apps.grading.services.graders.openai_client import OpenAIClient
from apps.core.exceptions import GradingError


class LLMGradingServiceTests(TestCase):
    """Tests for LLMGradingService with real question/answer scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_api_key = 'test-api-key-12345'
        self.user = create_test_user(email='student@example.com')
        self.exam = Exam.objects.create(
            title='Python Programming Test',
            course='CS101',
            duration_minutes=60,
            is_active=True
        )
        self.question1 = Question.objects.create(
            exam=self.exam,
            question_text='What is the capital of France?',
            question_type='SHORT_ANSWER',
            expected_answer='Paris',
            points=10,
            order=1
        )
        self.question2 = Question.objects.create(
            exam=self.exam,
            question_text='Explain the concept of photosynthesis.',
            question_type='ESSAY',
            expected_answer='Photosynthesis is the process by which plants convert light energy into chemical energy, producing glucose and oxygen from carbon dioxide and water.',
            points=20,
            order=2
        )
        self.question3 = Question.objects.create(
            exam=self.exam,
            question_text='What is 2 + 2?',
            question_type='SHORT_ANSWER',
            expected_answer='4',
            points=5,
            order=3
        )

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_correct_short_answer(self, mock_parse, mock_complete):
        """Test grading a correct short answer."""
        # Mock OpenAI response
        mock_response = {
            'content': '{"score": 10.0, "feedback": "Correct answer. The student correctly identified Paris as the capital of France."}',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 30, 'total_tokens': 80}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 10.0, 'feedback': 'Correct answer. The student correctly identified Paris as the capital of France.'}
        
        # Initialize service
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer
        result = service.grade_answer(
            answer_text='Paris',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify result
        self.assertEqual(result['score'], 10.0)
        self.assertIn('feedback', result)
        self.assertIn('Paris', result['feedback'])
        
        # Verify API was called
        mock_complete.assert_called_once()
        call_args = mock_complete.call_args
        self.assertIn('What is the capital of France?', call_args[1]['user_prompt'])
        self.assertIn('Paris', call_args[1]['user_prompt'])
        self.assertEqual(call_args[1]['model'], 'gpt-4.1')

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_partial_credit_essay(self, mock_parse, mock_complete):
        """Test grading an essay answer with partial credit."""
        # Mock OpenAI response
        mock_response = {
            'content': '{"score": 12.5, "feedback": "The student demonstrates basic understanding but misses key details like carbon dioxide, glucose production, and the conversion of light to chemical energy."}',
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 12.5, 'feedback': 'The student demonstrates basic understanding but misses key details like carbon dioxide, glucose production, and the conversion of light to chemical energy.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer
        result = service.grade_answer(
            answer_text='Photosynthesis is when plants make food using sunlight and water.',
            expected_answer='Photosynthesis is the process by which plants convert light energy into chemical energy, producing glucose and oxygen from carbon dioxide and water.',
            max_points=20,
            question_type='ESSAY',
            question_text='Explain the concept of photosynthesis.'
        )
        
        # Verify result
        self.assertGreater(result['score'], 0.0)
        self.assertLess(result['score'], 20.0)
        self.assertIn('feedback', result)
        
        # Verify API was called
        mock_complete.assert_called_once()

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_wrong_answer(self, mock_parse, mock_complete):
        """Test grading a completely wrong answer."""
        # Mock OpenAI response
        mock_response = {
            'content': '{"score": 0.0, "feedback": "Incorrect answer. The correct answer is 4."}',
            'usage': {'prompt_tokens': 40, 'completion_tokens': 20, 'total_tokens': 60}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 0.0, 'feedback': 'Incorrect answer. The correct answer is 4.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer
        result = service.grade_answer(
            answer_text='5',
            expected_answer='4',
            max_points=5,
            question_type='SHORT_ANSWER',
            question_text='What is 2 + 2?'
        )
        
        # Verify result
        self.assertEqual(result['score'], 0.0)
        self.assertIn('feedback', result)
        
        # Verify API was called
        mock_complete.assert_called_once()

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    def test_grade_empty_answer(self):
        """Test grading an empty answer returns zero without API call."""
        service = LLMGradingService()
        service.api_key = self.test_api_key
        
        # Grade empty answer
        result = service.grade_answer(
            answer_text='',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify result
        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['feedback'], 'No answer provided.')


    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_with_markdown_code_block_response(self, mock_parse, mock_complete):
        """Test grading when LLM returns JSON wrapped in markdown code blocks."""
        # Mock OpenAI response with markdown
        mock_response = {
            'content': '```json\n{"score": 9.5, "feedback": "Excellent answer with minor detail missing."}\n```',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 30, 'total_tokens': 80}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 9.5, 'feedback': 'Excellent answer with minor detail missing.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer
        result = service.grade_answer(
            answer_text='Paris is the capital and largest city of France.',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify result
        self.assertEqual(result['score'], 9.5)
        self.assertIn('feedback', result)
        
        # Verify parse_json_response was called (which handles markdown)
        mock_parse.assert_called()

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    def test_grade_api_error_raises_exception(self, mock_complete):
        """Test that API errors are properly raised."""
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Mock API error
        mock_complete.side_effect = Exception('API connection failed')
        
        # Grade answer should raise GradingError after retries
        with self.assertRaises(GradingError) as context:
            service.grade_answer(
                answer_text='Paris',
                expected_answer='Paris',
                max_points=10,
                question_type='SHORT_ANSWER',
                question_text='What is the capital of France?'
            )
        
        self.assertIn('LLM grading failed', str(context.exception))
        
        # Verify API was called max_retries times
        self.assertEqual(mock_complete.call_count, service.max_retries)


    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_answer_score_capped_at_max_points(self, mock_parse, mock_complete):
        """Test that scores are capped at max_points even if LLM returns higher."""
        # Mock OpenAI response with score higher than max_points
        mock_response = {
            'content': '{"score": 15.0, "feedback": "Perfect answer!"}',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 20, 'total_tokens': 70}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 15.0, 'feedback': 'Perfect answer!'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer with max_points=10
        result = service.grade_answer(
            answer_text='Paris',
            expected_answer='Paris',
            max_points=10,  # Max is 10, but LLM returned 15
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify score is capped at max_points
        self.assertLessEqual(result['score'], 10.0)

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_answer_score_never_negative(self, mock_parse, mock_complete):
        """Test that scores are never negative even if LLM returns negative."""
        # Mock OpenAI response with negative score
        mock_response = {
            'content': '{"score": -5.0, "feedback": "Wrong answer."}',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 20, 'total_tokens': 70}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': -5.0, 'feedback': 'Wrong answer.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade answer
        result = service.grade_answer(
            answer_text='Wrong answer',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text='What is the capital of France?'
        )
        
        # Verify score is never negative
        self.assertGreaterEqual(result['score'], 0.0)

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_answer_with_question_text_in_prompt(self, mock_parse, mock_complete):
        """Test that question_text is included in the grading prompt."""
        mock_response = {
            'content': '{"score": 10.0, "feedback": "Correct."}',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 20, 'total_tokens': 70}
        }
        mock_complete.return_value = mock_response
        mock_parse.return_value = {'score': 10.0, 'feedback': 'Correct.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        question_text = 'What is the capital of France?'
        
        # Grade answer
        service.grade_answer(
            answer_text='Paris',
            expected_answer='Paris',
            max_points=10,
            question_type='SHORT_ANSWER',
            question_text=question_text
        )
        
        # Verify question_text is in the prompt
        call_args = mock_complete.call_args
        self.assertIn(question_text, call_args[1]['user_prompt'])

    @patch.object(OpenAIClient, '__init__', lambda self, api_key=None: None)
    @patch.object(OpenAIClient, 'complete')
    @patch.object(OpenAIClient, 'parse_json_response')
    def test_grade_submission_handles_individual_errors(self, mock_parse, mock_complete):
        """Test that grading submission continues even if one question fails."""
        # Create submission
        session = ExamSession.objects.create(
            exam=self.exam,
            student=self.user
        )
        submission = Submission.objects.create(
            exam=self.exam,
            student=self.user,
            max_score=20.0,
            total_score=0.0,
            status='PENDING'
        )
        
        # Create answers
        answer1 = Answer.objects.create(
            submission=submission,
            question=self.question1,
            answer_text='Paris'
        )
        answer2 = Answer.objects.create(
            submission=submission,
            question=self.question2,
            answer_text='Some answer'
        )
        
        # Mock: first succeeds, second fails
        mock_responses = [
            {
                'content': '{"score": 10.0, "feedback": "Correct."}',
                'usage': {'prompt_tokens': 50, 'completion_tokens': 20, 'total_tokens': 70}
            },
            Exception('API Error for question 2')
        ]
        mock_complete.side_effect = mock_responses
        mock_parse.return_value = {'score': 10.0, 'feedback': 'Correct.'}
        
        service = LLMGradingService()
        service.api_key = self.test_api_key
        service.client = Mock()
        
        # Grade submission
        result = service.grade_submission(submission)
        
        # Verify result - should have graded first question, error for second
        self.assertEqual(result['status'], 'GRADED')
        self.assertEqual(result['total_score'], 10.0)  # Only first question scored
        self.assertEqual(len(result['answers']), 2)
        
        # First answer should have score, second should have error feedback
        self.assertEqual(result['answers'][0]['score'], 10.0)
        self.assertEqual(result['answers'][1]['score'], 0.0)
        self.assertIn('error', result['answers'][1]['feedback'].lower())

