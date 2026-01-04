"""Mock grading service using keyword matching and text similarity."""
import logging
import re
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .base import BaseGradingService
from apps.assessments.models import Submission

logger = logging.getLogger(__name__)


class MockGradingService(BaseGradingService):
    """Mock grading service using keyword matching and TF-IDF cosine similarity."""
    
    def __init__(self, keyword_weight=0.4, similarity_weight=0.6, similarity_threshold=0.3):
        self.keyword_weight = keyword_weight
        self.similarity_weight = similarity_weight
        self.similarity_threshold = similarity_threshold
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text."""
        normalized = self._normalize_text(text)
        words = normalized.split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        return keywords
    
    def _calculate_keyword_score(self, answer_text: str, expected_answer: str) -> float:
        """Calculate score based on keyword matching."""
        answer_keywords = self._extract_keywords(answer_text)
        expected_keywords = self._extract_keywords(expected_answer)
        
        if not expected_keywords:
            return 0.0
        
        matched_keywords = answer_keywords.intersection(expected_keywords)
        score = len(matched_keywords) / len(expected_keywords)
        return min(score, 1.0)
    
    def _calculate_similarity_score(self, answer_text: str, expected_answer: str) -> float:
        """Calculate score based on TF-IDF cosine similarity."""
        if not answer_text.strip() or not expected_answer.strip():
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([answer_text, expected_answer])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0
    
    def _generate_feedback(self, combined_score: float) -> str:
        """Generate feedback based on score."""
        if combined_score >= 0.8:
            return 'Excellent answer with strong keyword coverage and high similarity.'
        elif combined_score >= 0.6:
            return 'Good answer with adequate keyword coverage.'
        elif combined_score >= 0.4:
            return 'Fair answer with some relevant keywords.'
        elif combined_score >= 0.2:
            return 'Weak answer with minimal keyword coverage.'
        else:
            return 'Answer does not meet the expected criteria.'
    
    def grade_answer(
        self, 
        answer_text: str, 
        expected_answer: str, 
        max_points: int,
        question_type: str = 'SHORT_ANSWER',
        options: Optional[List] = None,
        allow_multiple: bool = False
    ) -> Dict:
        """Grade a single answer based on question type."""
        if not answer_text or not answer_text.strip():
            return {'score': 0.0, 'feedback': 'No answer provided.'}
        
        if question_type == 'MULTIPLE_CHOICE':
            return self._grade_multiple_choice(answer_text, expected_answer, max_points, allow_multiple)
        
        keyword_score = self._calculate_keyword_score(answer_text, expected_answer)
        similarity_score = self._calculate_similarity_score(answer_text, expected_answer)
        
        combined_score = (
            self.keyword_weight * keyword_score +
            self.similarity_weight * similarity_score
        )
        
        if combined_score < self.similarity_threshold:
            combined_score = 0.0
        
        final_score = round(combined_score * max_points, 2)
        feedback = self._generate_feedback(combined_score)
        
        return {'score': final_score, 'feedback': feedback}
    
    def grade_submission(self, submission: Submission) -> Dict:
        """Grade a complete submission."""
        logger.info(f'Grading submission {submission.id} using MockGradingService')
        answers_data = []
        total_score = 0.0
        
        answers = submission.answers.select_related('question').all()
        
        for answer in answers:
            question = answer.question
            grading_result = self.grade_answer(
                answer.answer_text,
                question.expected_answer,
                question.points,
                question_type=question.question_type,
                options=question.options,
                allow_multiple=question.allow_multiple
            )
            
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
