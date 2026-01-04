"""Response serializers for API documentation."""
from rest_framework import serializers


class SessionSubmitResponseSerializer(serializers.Serializer):
    """Response serializer for session submit endpoint."""
    grade_history_id = serializers.IntegerField()
    status = serializers.CharField()
    total_score = serializers.FloatField()
    max_score = serializers.FloatField()
    percentage = serializers.FloatField()


class AnswerSubmitResponseSerializer(serializers.Serializer):
    """Response serializer for single answer submit endpoint."""
    question_order = serializers.IntegerField()
    answer_text = serializers.CharField()
    answered_at = serializers.DateTimeField()
    progress = serializers.DictField()


class ProgressResponseSerializer(serializers.Serializer):
    """Response serializer for session progress endpoint."""
    total_questions = serializers.IntegerField()
    answered_count = serializers.IntegerField()
    answered_questions = serializers.ListField(child=serializers.IntegerField())
    current_question = serializers.IntegerField()
    time_remaining_seconds = serializers.IntegerField()
    is_expired = serializers.BooleanField()

