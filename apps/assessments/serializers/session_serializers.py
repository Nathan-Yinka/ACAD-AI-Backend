"""Serializers for exam sessions."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import ExamSession, SessionToken


class SessionTokenSerializer(serializers.ModelSerializer):
    """Serializer for session token (returned on start/continue)."""

    class Meta:
        model = SessionToken
        fields = ('token', 'created_at')
        read_only_fields = fields


class ExamSessionSerializer(serializers.ModelSerializer):
    """Serializer for exam session info."""
    time_remaining_seconds = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = ExamSession
        fields = (
            'id', 'exam', 'started_at', 'expires_at',
            'is_completed', 'submitted_at', 'time_remaining_seconds',
            'is_expired', 'is_active', 'answered_count', 'total_questions'
        )
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField())
    def get_time_remaining_seconds(self, obj):
        return obj.time_remaining_seconds()

    @extend_schema_field(serializers.BooleanField())
    def get_is_expired(self, obj):
        return obj.is_expired()

    @extend_schema_field(serializers.BooleanField())
    def get_is_active(self, obj):
        return obj.is_active()

    @extend_schema_field(serializers.IntegerField())
    def get_answered_count(self, obj):
        return obj.get_answered_count()

    @extend_schema_field(serializers.IntegerField())
    def get_total_questions(self, obj):
        return obj.get_total_questions()


class ExamSessionWithTokenSerializer(ExamSessionSerializer):
    """Session serializer that includes the token (for start/continue response)."""
    token = serializers.SerializerMethodField()

    class Meta(ExamSessionSerializer.Meta):
        fields = ExamSessionSerializer.Meta.fields + ('token',)

    @extend_schema_field(serializers.CharField())
    def get_token(self, obj):
        """Get the current valid token."""
        current_token = obj.get_current_token()
        return current_token.token if current_token else None
