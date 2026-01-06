from rest_framework import serializers
from ..models import Answer
from .question_serializers import QuestionDetailSerializer


class AnswerCreateSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'Question ID is required.',
            'invalid': 'Question ID must be a valid integer.',
        }
    )
    answer_text = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text='Answer text. For multiple choice with allow_multiple=True, use JSON array like ["A", "B"]',
        error_messages={
            'required': 'Answer text is required.',
            'blank': 'Answer text cannot be blank.',
        }
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

