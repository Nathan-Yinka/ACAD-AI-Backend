#!/usr/bin/env python
"""
Test script for LLM Grader - Test the OpenAI grading service with real questions and answers.

Usage:
    python test_llm_grader.py
    
    Or with arguments:
    python test_llm_grader.py "What is the capital of France?" "Paris" "Paris" 10
"""
import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import logging
from apps.grading.services.graders.llm_grading import LLMGradingService
from apps.core.exceptions import GradingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_llm_grader(question_text, expected_answer, student_answer, max_points=10):
    """
    Test the LLM grader with a question and answer.
    
    Args:
        question_text: The question being asked
        expected_answer: The correct/expected answer
        student_answer: The student's answer to grade
        max_points: Maximum points for this question (default: 10)
    """
    print("\n" + "="*80)
    print("LLM GRADER TEST")
    print("="*80)
    print(f"\nQuestion: {question_text}")
    print(f"Expected Answer: {expected_answer}")
    print(f"Student Answer: {student_answer}")
    print(f"Maximum Points: {max_points}")
    print("\n" + "-"*80)
    
    try:
        # Initialize the LLM grading service
        print("Initializing LLM Grading Service...")
        service = LLMGradingService()
        print("✓ Service initialized successfully\n")
        
        # Grade the answer
        print("Sending request to OpenAI API...")
        logger.info(f"Grading question: {question_text}")
        logger.info(f"Expected: {expected_answer}, Student: {student_answer}, Max: {max_points}")
        
        result = service.grade_answer(
            answer_text=student_answer,
            expected_answer=expected_answer,
            max_points=max_points,
            question_type='SHORT_ANSWER',
            question_text=question_text
        )
        
        # Display results
        print("\n" + "="*80)
        print("GRADING RESULTS")
        print("="*80)
        print(f"\nScore: {result['score']}/{max_points}")
        print(f"Percentage: {(result['score']/max_points)*100:.1f}%")
        print(f"\nFeedback:\n{result['feedback']}")
        print("\n" + "="*80)
        
        # Log the results
        logger.info(f"Grading completed - Score: {result['score']}/{max_points}")
        logger.info(f"Feedback: {result['feedback']}")
        
        return result
        
    except GradingError as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.error(f"Grading error: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return None


def interactive_mode():
    """Run in interactive mode, prompting for input."""
    print("\n" + "="*80)
    print("LLM GRADER TEST - Interactive Mode")
    print("="*80)
    print("\nEnter the question and answers to test the LLM grader.\n")
    
    question_text = input("Question: ").strip()
    if not question_text:
        print("❌ Question cannot be empty!")
        return
    
    expected_answer = input("Expected Answer: ").strip()
    if not expected_answer:
        print("❌ Expected answer cannot be empty!")
        return
    
    student_answer = input("Student Answer: ").strip()
    if not student_answer:
        print("❌ Student answer cannot be empty!")
        return
    
    max_points_input = input("Maximum Points (default: 10): ").strip()
    max_points = int(max_points_input) if max_points_input else 10
    
    test_llm_grader(question_text, expected_answer, student_answer, max_points)


def main():
    """Main entry point."""
    # Check if API key is configured
    from django.conf import settings
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')
    
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not configured!")
        print("Please set OPENAI_API_KEY in your .env file or environment variables.")
        sys.exit(1)
    
    # Check if arguments are provided
    if len(sys.argv) == 5:
        # Command line arguments: question, expected, student, max_points
        question_text = sys.argv[1]
        expected_answer = sys.argv[2]
        student_answer = sys.argv[3]
        max_points = int(sys.argv[4])
        test_llm_grader(question_text, expected_answer, student_answer, max_points)
    elif len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    else:
        print("\nUsage:")
        print("  python test_llm_grader.py")
        print("  python test_llm_grader.py \"Question\" \"Expected Answer\" \"Student Answer\" max_points")
        print("\nExample:")
        print("  python test_llm_grader.py \"What is the capital of France?\" \"Paris\" \"Paris\" 10")
        sys.exit(1)


if __name__ == '__main__':
    main()

