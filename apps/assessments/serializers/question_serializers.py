from rest_framework import serializers
from ..models import Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'question_type', 'points', 'order', 'options', 'allow_multiple')
        read_only_fields = ('id',)


class QuestionDetailSerializer(serializers.ModelSerializer):
    allow_multiple = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Question
        fields = ('id', 'question_text', 'question_type', 'points', 'order', 'options', 'allow_multiple')

