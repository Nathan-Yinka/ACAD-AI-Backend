from rest_framework import serializers
from ..models import Answer
from .question_serializers import QuestionDetailSerializer


class AnswerCreateSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(write_only=True)
    answer_text = serializers.CharField(
        help_text='Answer text. For multiple choice with allow_multiple=True, use JSON array like ["A", "B"]'
    )

    class Meta:
        model = Answer
        fields = ('question_id', 'answer_text')
        read_only_fields = ('score', 'graded_at')


class AnswerDetailSerializer(serializers.ModelSerializer):
    question = QuestionDetailSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ('id', 'question', 'answer_text', 'score', 'graded_at')
        read_only_fields = ('id', 'score', 'graded_at')

