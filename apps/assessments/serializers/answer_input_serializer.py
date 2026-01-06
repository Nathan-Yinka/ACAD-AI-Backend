"""Serializer for answer input in session answer endpoint."""
from rest_framework import serializers


class AnswerTextInputSerializer(serializers.Serializer):
    """Serializer for answer_text input in SessionAnswerView."""
    answer_text = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Answer text is required.',
            'blank': 'Answer text cannot be blank.',
        }
    )

