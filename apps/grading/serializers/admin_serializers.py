"""Admin serializers for detailed grade viewing."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.grading.models import GradeHistory
from apps.assessments.models import ExamSession, StudentAnswer, Question


class AdminQuestionDetailSerializer(serializers.ModelSerializer):
    """Full question details for admin view."""
    
    class Meta:
        model = Question
        fields = (
            'id', 'order', 'question_text', 'question_type',
            'expected_answer', 'options', 'allow_multiple', 'points'
        )


class AdminStudentAnswerSerializer(serializers.ModelSerializer):
    """Student answer with full question details for admin."""
    question = AdminQuestionDetailSerializer(read_only=True)

    class Meta:
        model = StudentAnswer
        fields = ('id', 'question', 'answer_text', 'answered_at')


class AdminSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed session view for admin including all answers."""
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    student_answers = AdminStudentAnswerSerializer(many=True, read_only=True)
    answered_count = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ExamSession
        fields = (
            'id', 'student', 'student_email', 'student_name',
            'exam', 'exam_title', 'started_at', 'expires_at',
            'is_completed', 'submitted_at', 'submission_type',
            'answered_count', 'total_questions', 'time_remaining_seconds',
            'student_answers'
        )

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'.strip() or obj.student.email

    @extend_schema_field(serializers.IntegerField())
    def get_answered_count(self, obj):
        return obj.get_answered_count()

    @extend_schema_field(serializers.IntegerField())
    def get_total_questions(self, obj):
        return obj.get_total_questions()

    @extend_schema_field(serializers.IntegerField())
    def get_time_remaining_seconds(self, obj):
        return obj.time_remaining_seconds()


class AdminSessionListSerializer(serializers.ModelSerializer):
    """Session list view for admin."""
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ExamSession
        fields = (
            'id', 'student', 'student_email', 'student_name',
            'started_at', 'expires_at', 'is_completed', 'submitted_at',
            'submission_type', 'answered_count', 'total_questions', 'is_expired'
        )

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'.strip() or obj.student.email

    @extend_schema_field(serializers.IntegerField())
    def get_answered_count(self, obj):
        return obj.get_answered_count()

    @extend_schema_field(serializers.IntegerField())
    def get_total_questions(self, obj):
        return obj.get_total_questions()

    @extend_schema_field(serializers.BooleanField())
    def get_is_expired(self, obj):
        return obj.is_expired()


class AdminGradeDetailSerializer(serializers.ModelSerializer):
    """Detailed grade view for admin with full question and answer data."""
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    course = serializers.CharField(source='exam.course', read_only=True)

    class Meta:
        model = GradeHistory
        fields = (
            'id', 'student', 'student_email', 'student_name',
            'exam', 'exam_title', 'course', 'session_id',
            'status', 'total_score', 'max_score', 'percentage',
            'answers_data', 'started_at', 'submitted_at', 'graded_at',
            'grading_method', 'created_at'
        )

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'.strip() or obj.student.email


class AdminGradeListSerializer(serializers.ModelSerializer):
    """Grade list view for admin."""
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    exam_title = serializers.CharField(source='exam.title', read_only=True)

    class Meta:
        model = GradeHistory
        fields = (
            'id', 'student', 'student_email', 'student_name',
            'exam', 'exam_title', 'status', 'total_score',
            'max_score', 'percentage', 'grading_method', 'submitted_at'
        )

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'.strip() or obj.student.email

