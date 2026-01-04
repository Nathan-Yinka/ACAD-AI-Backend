from django.contrib import admin
from .models import Exam, Question, Submission, Answer, ExamSession, SessionToken, StudentAnswer


class QuestionInline(admin.StackedInline):
    """
    Inline admin for Questions within Exam admin.
    Using StackedInline for better display of complex fields like options (JSONField).
    """
    model = Question
    extra = 1
    fields = ('order', 'question_text', 'question_type', 'points', 'options', 'allow_multiple', 'expected_answer')
    verbose_name = 'Question'
    verbose_name_plural = 'Questions'


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """
    Admin interface for Exam model.
    """
    list_display = ('title', 'course', 'duration_minutes', 'is_active', 'created_at', 'get_questions_count')
    list_filter = ('is_active', 'course', 'created_at')
    search_fields = ('title', 'description', 'course')
    ordering = ('-created_at',)
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'course')
        }),
        ('Settings', {
            'fields': ('duration_minutes', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()
    get_questions_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model.
    """
    list_display = ('__str__', 'exam', 'question_type', 'points', 'order')
    list_filter = ('question_type', 'exam', 'points')
    search_fields = ('question_text', 'exam__title')
    ordering = ('exam', 'order')
    
    fieldsets = (
        ('Question Details', {
            'fields': ('exam', 'order', 'question_text', 'question_type', 'points')
        }),
        ('Options (for Multiple Choice)', {
            'fields': ('options', 'allow_multiple'),
            'description': 'Enter options as JSON array of objects: [{"label": "A", "value": "Paris"}, {"label": "B", "value": "London"}]'
        }),
        ('Answer Key', {
            'fields': ('expected_answer',),
            'description': 'For single answer: "A". For multiple answers: ["A", "B"]'
        }),
    )


class AnswerInline(admin.TabularInline):
    """
    Inline admin for Answers within Submission admin.
    """
    model = Answer
    extra = 0
    readonly_fields = ('question', 'answer_text', 'score', 'graded_at')
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """
    Admin interface for Submission model.
    """
    list_display = (
        'id', 'student', 'exam', 'status', 'total_score',
        'max_score', 'submitted_at', 'graded_at'
    )
    list_filter = ('status', 'submitted_at', 'graded_at', 'exam')
    search_fields = ('student__email', 'student__username', 'exam__title')
    ordering = ('-submitted_at',)
    readonly_fields = ('submitted_at', 'graded_at', 'calculate_percentage_display')
    inlines = [AnswerInline]
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('student', 'exam', 'status')
        }),
        ('Scores', {
            'fields': ('total_score', 'max_score', 'calculate_percentage_display')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'graded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def calculate_percentage_display(self, obj):
        return f'{obj.calculate_percentage()}%'
    calculate_percentage_display.short_description = 'Percentage'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """
    Admin interface for Answer model.
    """
    list_display = ('id', 'submission', 'question', 'score', 'graded_at')
    list_filter = ('graded_at', 'question__question_type', 'question__exam')
    search_fields = ('answer_text', 'submission__student__email', 'question__question_text')
    ordering = ('-submission__submitted_at', 'question__order')
    readonly_fields = ('submission', 'question', 'answer_text', 'score', 'graded_at')
    
    fieldsets = (
        ('Answer Information', {
            'fields': ('submission', 'question')
        }),
        ('Answer Content', {
            'fields': ('answer_text',)
        }),
        ('Grading', {
            'fields': ('score', 'graded_at')
        }),
    )


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for ExamSession model.
    """
    list_display = ('id', 'student', 'exam', 'started_at', 'expires_at', 'is_completed', 'is_expired_display')
    list_filter = ('is_completed', 'started_at', 'exam')
    search_fields = ('student__email', 'exam__title')
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'expires_at', 'is_expired_display', 'time_remaining_display')
    
    fieldsets = (
        ('Session Information', {
            'fields': ('student', 'exam', 'is_completed')
        }),
        ('Timing', {
            'fields': ('started_at', 'expires_at', 'submitted_at', 'time_remaining_display', 'is_expired_display')
        }),
    )
    
    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expired'
    
    def time_remaining_display(self, obj):
        seconds = obj.time_remaining_seconds()
        if seconds <= 0:
            return 'Expired'
        minutes = seconds // 60
        secs = seconds % 60
        return f'{minutes}m {secs}s'
    time_remaining_display.short_description = 'Time Remaining'


class StudentAnswerInline(admin.TabularInline):
    """Inline admin for StudentAnswer within ExamSession admin."""
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'answer_text', 'answered_at')


class SessionTokenInline(admin.TabularInline):
    """Inline admin for SessionToken within ExamSession admin."""
    model = SessionToken
    extra = 0
    readonly_fields = ('token', 'is_valid', 'created_at', 'invalidated_at')
    can_delete = False


@admin.register(SessionToken)
class SessionTokenAdmin(admin.ModelAdmin):
    """Admin interface for SessionToken model."""
    list_display = ('id', 'session', 'token_display', 'is_valid', 'created_at', 'invalidated_at')
    list_filter = ('is_valid', 'created_at')
    search_fields = ('token', 'session__student__email')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'session', 'created_at', 'invalidated_at')

    def token_display(self, obj):
        return f'{obj.token[:12]}...'
    token_display.short_description = 'Token'


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    """Admin interface for StudentAnswer model."""
    list_display = ('id', 'session', 'question', 'answered_at')
    list_filter = ('answered_at', 'session__exam')
    search_fields = ('session__student__email', 'question__question_text')
    ordering = ('-answered_at',)
    readonly_fields = ('answered_at',)

