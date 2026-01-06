from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import Submission
from .answer_serializers import AnswerCreateSerializer, AnswerDetailSerializer
from .exam_serializers import ExamDetailSerializer
from apps.core.exceptions import SubmissionValidationError
from apps.assessments.services.answer_service import AnswerService


class SubmissionCreateSerializer(serializers.Serializer):
    answers = AnswerCreateSerializer(
        many=True,
        required=True,
        error_messages={
            'required': 'Answers are required.',
            'null': 'Answers cannot be null.',
            'not_a_list': 'Answers must be a list.',
            'empty': 'At least one answer is required.',
        }
    )

    def validate_answers(self, value):
        """Validate all answers using AnswerService normalization."""
        if not value:
            raise serializers.ValidationError('At least one answer is required.')
        
        question_ids = [ans['question_id'] for ans in value]
        from ..models import Question
        
        questions = Question.objects.filter(id__in=question_ids).select_related('exam')
        question_map = {q.id: q for q in questions}
        
        for answer_data in value:
            question_id = answer_data['question_id']
            question = question_map.get(question_id)
            
            if question:
                answer_text = answer_data.get('answer_text', '')
                try:
                    AnswerService.normalize_answer(question, answer_text)
                except SubmissionValidationError as e:
                    raise serializers.ValidationError({'answers': str(e)})
        
        return value


class SubmissionListSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = (
            'id', 'exam', 'exam_title', 'submitted_at', 'graded_at',
            'total_score', 'max_score', 'status', 'percentage'
        )
        read_only_fields = (
            'id', 'submitted_at', 'graded_at', 'total_score',
            'max_score', 'status', 'percentage'
        )

    @extend_schema_field(serializers.FloatField())
    def get_percentage(self, obj):
        """Return the percentage score for the submission."""
        return obj.calculate_percentage()


class SubmissionDetailSerializer(serializers.ModelSerializer):
    exam = ExamDetailSerializer(read_only=True)
    answers = AnswerDetailSerializer(many=True, read_only=True)
    percentage = serializers.SerializerMethodField()
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model = Submission
        fields = (
            'id', 'student', 'student_email', 'exam', 'submitted_at',
            'graded_at', 'total_score', 'max_score', 'status',
            'answers', 'percentage'
        )
        read_only_fields = (
            'id', 'student', 'submitted_at', 'graded_at',
            'total_score', 'max_score', 'status', 'percentage'
        )

    @extend_schema_field(serializers.FloatField())
    def get_percentage(self, obj):
        """Return the percentage score for the submission."""
        return obj.calculate_percentage()

