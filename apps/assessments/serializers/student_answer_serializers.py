"""Serializers for student answers during exam sessions."""
from rest_framework import serializers
from ..models import StudentAnswer


class StudentAnswerSerializer(serializers.ModelSerializer):
    """Serializer for student answers during a session."""
    question_order = serializers.IntegerField(source='question.order', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = StudentAnswer
        fields = ('id', 'question', 'question_order', 'question_text', 'answer_text', 'answered_at')
        read_only_fields = ('id', 'question', 'answered_at')

