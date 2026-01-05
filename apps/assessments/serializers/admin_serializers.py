"""Admin serializers for the assessments app."""
from django.db import models
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import Exam, Question


class AdminQuestionSerializer(serializers.ModelSerializer):
    """Admin serializer for Question model (includes expected_answer, options, and allow_multiple)."""
    class Meta:
        model = Question
        fields = (
            'id', 'exam', 'question_text', 'question_type',
            'expected_answer', 'options', 'allow_multiple', 'points', 'order'
        )
        read_only_fields = ('id', 'exam', 'order')
    
    def create(self, validated_data):
        """Auto-increment order based on existing questions for the exam."""
        exam = self.context.get('exam') or validated_data.get('exam')
        if not exam:
            raise serializers.ValidationError({'exam': 'Exam is required'})
        max_order = exam.questions.aggregate(max_order=models.Max('order'))['max_order']
        validated_data['order'] = (max_order or 0) + 1
        validated_data['exam'] = exam
        return super().create(validated_data)
    
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
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_active')
    
    def create(self, validated_data):
        """Force is_active to False on creation."""
        validated_data['is_active'] = False
        return super().create(validated_data)


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

