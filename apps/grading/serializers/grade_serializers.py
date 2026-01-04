"""Serializers for the grading app (student view)."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.grading.models import GradeHistory


class GradeHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing grade history (student view)."""
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    course = serializers.CharField(source='exam.course', read_only=True)

    class Meta:
        model = GradeHistory
        fields = (
            'id', 'exam', 'exam_title', 'course', 'status',
            'total_score', 'max_score', 'percentage',
            'started_at', 'submitted_at', 'graded_at',
            'grading_method', 'created_at'
        )
        read_only_fields = fields


class QuestionScoreSerializer(serializers.Serializer):
    """Serializer for individual question scores."""
    question_order = serializers.IntegerField()
    score = serializers.FloatField()
    max_score = serializers.FloatField()


class GradeHistoryDetailSerializer(serializers.ModelSerializer):
    """Detailed grade history for student (scores only, no answers)."""
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    course = serializers.CharField(source='exam.course', read_only=True)
    question_scores = serializers.SerializerMethodField()

    class Meta:
        model = GradeHistory
        fields = (
            'id', 'exam', 'exam_title', 'course', 'status',
            'total_score', 'max_score', 'percentage',
            'question_scores',
            'started_at', 'submitted_at', 'graded_at',
            'grading_method', 'created_at'
        )
        read_only_fields = fields

    @extend_schema_field(QuestionScoreSerializer(many=True))
    def get_question_scores(self, obj):
        """Return only question order and scores, not the full answer data."""
        if not obj.answers_data:
            return []
        
        return [
            {
                'question_order': item.get('question_order'),
                'score': item.get('score'),
                'max_score': item.get('max_score'),
            }
            for item in obj.answers_data
            if isinstance(item, dict)
        ]

