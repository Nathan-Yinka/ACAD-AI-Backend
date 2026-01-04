from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import Exam


class ExamListSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = (
            'id', 'title', 'description', 'duration_minutes',
            'course', 'created_at', 'questions_count'
        )
        read_only_fields = ('id', 'created_at', 'questions_count')

    @extend_schema_field(serializers.IntegerField())
    def get_questions_count(self, obj):
        """Return the count of questions in the exam."""
        return obj.get_questions_count()


class ExamDetailSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = (
            'id', 'title', 'description', 'duration_minutes',
            'course', 'created_at', 'updated_at',
            'questions_count', 'max_score'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    @extend_schema_field(serializers.IntegerField())
    def get_questions_count(self, obj):
        """Return the count of questions in the exam."""
        return obj.get_questions_count()

    @extend_schema_field(serializers.FloatField())
    def get_max_score(self, obj):
        """Return the maximum possible score for the exam."""
        return float(obj.get_max_score())

