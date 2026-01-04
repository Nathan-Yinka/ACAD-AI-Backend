"""Tests for grading different question types."""
import json
from django.test import TestCase
from apps.grading.services.graders.mock_grading import MockGradingService


class QuestionTypeGradingTests(TestCase):
    """Tests for grading different question types."""
    
    def setUp(self):
        self.service = MockGradingService()
    
    def test_short_answer_exact_match(self):
        """Test short answer with exact match."""
        result = self.service.grade_answer(
            answer_text='Python is a programming language',
            expected_answer='Python is a programming language',
            max_points=10,
            question_type='SHORT_ANSWER'
        )
        self.assertEqual(result['score'], 10.0)
        self.assertIn('Excellent', result['feedback'])
    
    def test_short_answer_partial_match(self):
        """Test short answer with partial match."""
        result = self.service.grade_answer(
            answer_text='Python is a language',
            expected_answer='Python is a high-level programming language',
            max_points=10,
            question_type='SHORT_ANSWER'
        )
        self.assertGreater(result['score'], 0.0)
        self.assertLess(result['score'], 10.0)
        self.assertIn('feedback', result)
    
    def test_essay_exact_match(self):
        """Test essay with exact match."""
        result = self.service.grade_answer(
            answer_text='Django is a web framework for Python',
            expected_answer='Django is a web framework for Python',
            max_points=20,
            question_type='ESSAY'
        )
        self.assertEqual(result['score'], 20.0)
        self.assertIn('Excellent', result['feedback'])
    
    def test_essay_partial_match(self):
        """Test essay with partial match."""
        result = self.service.grade_answer(
            answer_text='Django is a framework',
            expected_answer='Django is a high-level Python web framework',
            max_points=20,
            question_type='ESSAY'
        )
        self.assertGreater(result['score'], 0.0)
        self.assertLess(result['score'], 20.0)
        self.assertIn('feedback', result)
    
    def test_mcq_single_correct(self):
        """Test MCQ single choice with correct answer."""
        result = self.service.grade_answer(
            answer_text='opt1',
            expected_answer='opt1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            allow_multiple=False
        )
        self.assertEqual(result['score'], 5.0)
        self.assertIn('Correct', result['feedback'])
    
    def test_mcq_single_incorrect(self):
        """Test MCQ single choice with incorrect answer."""
        result = self.service.grade_answer(
            answer_text='opt2',
            expected_answer='opt1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            options=[{'label': 'A', 'value': 'opt1'}, {'label': 'B', 'value': 'opt2'}],
            allow_multiple=False
        )
        self.assertEqual(result['score'], 0.0)
        self.assertIn('Incorrect', result['feedback'])
    
    def test_mcq_multiple_all_correct(self):
        """Test MCQ multiple choice with all correct answers."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student = json.dumps(['opt1', 'opt2', 'opt3'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'},
                {'label': 'D', 'value': 'opt4'}
            ],
            allow_multiple=True
        )
        self.assertEqual(result['score'], 10.0)
        self.assertIn('All correct', result['feedback'])
    
    def test_mcq_multiple_partial_correct(self):
        """Test MCQ multiple choice with partial correct answers."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student = json.dumps(['opt1', 'opt2'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'},
                {'label': 'D', 'value': 'opt4'}
            ],
            allow_multiple=True
        )
        expected_score = round((2 / 3) * 10, 2)
        self.assertEqual(result['score'], expected_score)
        self.assertIn('2 out of 3', result['feedback'])
    
    def test_mcq_multiple_with_incorrect(self):
        """Test MCQ multiple choice with correct and incorrect answers."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student = json.dumps(['opt1', 'opt2', 'opt4'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'},
                {'label': 'D', 'value': 'opt4'}
            ],
            allow_multiple=True
        )
        correct_score = (2 / 3) * 10
        penalty = (1 / 3) * 10
        expected_score = round(max(0.0, correct_score - penalty), 2)
        self.assertEqual(result['score'], expected_score)
        self.assertIn('2 out of 3', result['feedback'])
    
    def test_mcq_multiple_no_correct(self):
        """Test MCQ multiple choice with no correct answers."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student = json.dumps(['opt4', 'opt5'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            options=[
                {'label': 'A', 'value': 'opt1'},
                {'label': 'B', 'value': 'opt2'},
                {'label': 'C', 'value': 'opt3'},
                {'label': 'D', 'value': 'opt4'}
            ],
            allow_multiple=True
        )
        self.assertEqual(result['score'], 0.0)
        self.assertIn('Incorrect', result['feedback'])
    
    def test_mcq_single_stored_as_string(self):
        """Test that MCQ single answer is stored as plain string."""
        result = self.service.grade_answer(
            answer_text='opt1',
            expected_answer='opt1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=False
        )
        self.assertEqual(result['score'], 5.0)
    
    def test_mcq_multiple_stored_as_json_string(self):
        """Test that MCQ multiple answers are stored as JSON string."""
        student_answer = json.dumps(['opt1', 'opt2'])
        expected_answer = json.dumps(['opt1', 'opt2', 'opt3'])
        result = self.service.grade_answer(
            answer_text=student_answer,
            expected_answer=expected_answer,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        self.assertGreater(result['score'], 0.0)
        self.assertLess(result['score'], 10.0)
    
    def test_short_answer_stored_as_plain_text(self):
        """Test that short answer is stored as plain text."""
        result = self.service.grade_answer(
            answer_text='Python is a programming language',
            expected_answer='Python is a high-level programming language',
            max_points=10,
            question_type='SHORT_ANSWER'
        )
        self.assertGreater(result['score'], 0.0)
        self.assertIn('feedback', result)
    
    def test_essay_stored_as_plain_text(self):
        """Test that essay is stored as plain text."""
        result = self.service.grade_answer(
            answer_text='Django is a web framework for building web applications',
            expected_answer='Django is a high-level Python web framework',
            max_points=20,
            question_type='ESSAY'
        )
        self.assertGreater(result['score'], 0.0)
        self.assertIn('feedback', result)
    
    def test_mcq_single_case_sensitive(self):
        """Test that MCQ single choice is case sensitive (exact match)."""
        result = self.service.grade_answer(
            answer_text='opt1',
            expected_answer='OPT1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=False
        )
        self.assertEqual(result['score'], 0.0)
    
    def test_mcq_multiple_order_does_not_matter(self):
        """Test that MCQ multiple choice order doesn't matter."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student1 = json.dumps(['opt1', 'opt2', 'opt3'])
        student2 = json.dumps(['opt3', 'opt2', 'opt1'])
        
        result1 = self.service.grade_answer(
            answer_text=student1,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        
        result2 = self.service.grade_answer(
            answer_text=student2,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        
        self.assertEqual(result1['score'], result2['score'])
        self.assertEqual(result1['score'], 10.0)
    
    def test_short_answer_empty_string(self):
        """Test short answer with empty string."""
        result = self.service.grade_answer(
            answer_text='',
            expected_answer='Python is a programming language',
            max_points=10,
            question_type='SHORT_ANSWER'
        )
        self.assertEqual(result['score'], 0.0)
        self.assertIn('No answer', result['feedback'])
    
    def test_mcq_single_empty_string(self):
        """Test MCQ single choice with empty string."""
        result = self.service.grade_answer(
            answer_text='',
            expected_answer='opt1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=False
        )
        self.assertEqual(result['score'], 0.0)
    
    def test_mcq_multiple_one_correct_one_wrong(self):
        """Test MCQ multiple with 1 correct and 1 wrong out of 3 expected."""
        expected = json.dumps(['opt1', 'opt2', 'opt3'])
        student = json.dumps(['opt1', 'opt4'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        correct_score = (1 / 3) * 10
        penalty = (1 / 3) * 10
        expected_score = round(max(0.0, correct_score - penalty), 2)
        self.assertEqual(result['score'], expected_score)
    
    def test_mcq_single_stored_format_verification(self):
        """Verify MCQ single answer is stored as plain string (not JSON)."""
        result = self.service.grade_answer(
            answer_text='opt1',
            expected_answer='opt1',
            max_points=5,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=False
        )
        self.assertEqual(result['score'], 5.0)
        self.assertIsInstance('opt1', str)
    
    def test_mcq_multiple_stored_format_verification(self):
        """Verify MCQ multiple answers are stored as JSON string."""
        student_answer = json.dumps(['opt1', 'opt2'])
        expected_answer = json.dumps(['opt1', 'opt2', 'opt3'])
        result = self.service.grade_answer(
            answer_text=student_answer,
            expected_answer=expected_answer,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        self.assertIsInstance(student_answer, str)
        parsed = json.loads(student_answer)
        self.assertIsInstance(parsed, list)
        self.assertEqual(result['score'], round((2 / 3) * 10, 2))
    
    def test_short_answer_stored_format_verification(self):
        """Verify short answer is stored as plain text (not JSON)."""
        answer = 'Python is a programming language'
        result = self.service.grade_answer(
            answer_text=answer,
            expected_answer='Python is a high-level programming language',
            max_points=10,
            question_type='SHORT_ANSWER'
        )
        self.assertIsInstance(answer, str)
        self.assertGreater(result['score'], 0.0)
    
    def test_essay_stored_format_verification(self):
        """Verify essay is stored as plain text (not JSON)."""
        answer = 'Django is a web framework for building web applications'
        result = self.service.grade_answer(
            answer_text=answer,
            expected_answer='Django is a high-level Python web framework',
            max_points=20,
            question_type='ESSAY'
        )
        self.assertIsInstance(answer, str)
        self.assertGreater(result['score'], 0.0)
    
    def test_mcq_multiple_all_wrong(self):
        """Test MCQ multiple with all wrong answers."""
        expected = json.dumps(['opt1', 'opt2'])
        student = json.dumps(['opt3', 'opt4'])
        result = self.service.grade_answer(
            answer_text=student,
            expected_answer=expected,
            max_points=10,
            question_type='MULTIPLE_CHOICE',
            allow_multiple=True
        )
        penalty = (2 / 2) * 10
        expected_score = round(max(0.0, 0 - penalty), 2)
        self.assertEqual(result['score'], expected_score)
        self.assertIn('Incorrect', result['feedback'])

