from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Exam, Question, ExamSession


class AdminQuestionSerializer(serializers.ModelSerializer):
    """Admin serializer for Question model (includes expected_answer, options, and allow_multiple)."""
    class Meta:
        model = Question
        fields = (
            'id', 'exam', 'question_text', 'question_type',
            'expected_answer', 'options', 'allow_multiple', 'points', 'order'
        )
        read_only_fields = ('id',)
    
    def validate(self, data):
        """Validate question based on type."""
        import json
        question_type = data.get('question_type', self.instance.question_type if self.instance else 'SHORT_ANSWER')
        options = data.get('options', self.instance.options if self.instance else [])
        expected_answer = data.get('expected_answer', self.instance.expected_answer if self.instance else '')
        allow_multiple = data.get('allow_multiple', self.instance.allow_multiple if self.instance else False)
        
        if question_type == 'MULTIPLE_CHOICE':
            if not options or len(options) < 2:
                raise serializers.ValidationError({
                    'options': 'Multiple choice questions must have at least 2 options.'
                })
            if not isinstance(options, list):
                raise serializers.ValidationError({
                    'options': 'Options must be a list.'
                })
            
            # Validate options structure
            option_values = []
            for idx, option in enumerate(options):
                if not isinstance(option, dict):
                    raise serializers.ValidationError({
                        'options': f'Option {idx} must be an object with "label" and "value" keys.'
                    })
                if 'label' not in option or 'value' not in option:
                    raise serializers.ValidationError({
                        'options': f'Option {idx} must have both "label" and "value" keys.'
                    })
                option_values.append(option['value'])
            
            # Validate expected_answer
            if expected_answer:
                try:
                    expected_answers = json.loads(expected_answer)
                    if not isinstance(expected_answers, list):
                        expected_answers = [expected_answer]
                except (json.JSONDecodeError, TypeError):
                    expected_answers = [expected_answer]
                
                for expected in expected_answers:
                    if expected not in option_values:
                        raise serializers.ValidationError({
                            'expected_answer': f'Expected answer "{expected}" must be one of the option values: {", ".join(option_values)}'
                        })
                
                # If allow_multiple is False, only one answer allowed
                if not allow_multiple and len(expected_answers) > 1:
                    raise serializers.ValidationError({
                        'expected_answer': 'Multiple answers provided but allow_multiple is False.'
                    })
        
        # Validate allow_multiple only for MULTIPLE_CHOICE
        if allow_multiple and question_type != 'MULTIPLE_CHOICE':
            raise serializers.ValidationError({
                'allow_multiple': 'allow_multiple can only be True for MULTIPLE_CHOICE questions.'
            })
        
        return data


class AdminExamSerializer(serializers.ModelSerializer):
    """Admin serializer for creating/updating Exam model."""
    class Meta:
        model = Exam
        fields = (
            'id', 'title', 'description', 'duration_minutes',
            'course', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class AdminExamDetailSerializer(serializers.ModelSerializer):
    """Admin serializer for Exam with questions (includes expected answers)."""
    questions = AdminQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    max_score = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = (
            'id', 'title', 'description', 'duration_minutes',
            'course', 'is_active', 'created_at', 'updated_at',
            'questions', 'questions_count', 'max_score'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'questions_count', 'max_score')

    @extend_schema_field(serializers.IntegerField())
    def get_questions_count(self, obj):
        return obj.get_questions_count()

    @extend_schema_field(serializers.FloatField())
    def get_max_score(self, obj):
        return float(obj.get_max_score())


class ExamSessionSerializer(serializers.ModelSerializer):
    """Serializer for ExamSession model."""
    time_remaining_seconds = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ExamSession
        fields = (
            'id', 'exam', 'started_at', 'expires_at',
            'is_completed', 'submitted_at', 'time_remaining_seconds', 'is_expired'
        )
        read_only_fields = ('id', 'started_at', 'expires_at', 'is_completed', 'submitted_at')

    @extend_schema_field(serializers.IntegerField())
    def get_time_remaining_seconds(self, obj):
        return obj.time_remaining_seconds()

    @extend_schema_field(serializers.BooleanField())
    def get_is_expired(self, obj):
        return obj.is_expired()

