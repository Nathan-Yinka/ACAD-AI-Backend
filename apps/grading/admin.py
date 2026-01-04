"""Admin configuration for the grading app."""
from django.contrib import admin
from .models import GradeHistory


@admin.register(GradeHistory)
class GradeHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'exam', 'status', 'total_score',
        'max_score', 'percentage', 'grading_method', 'created_at'
    )
    list_filter = ('status', 'grading_method', 'created_at', 'exam')
    search_fields = ('student__email', 'exam__title')
    ordering = ('-created_at',)
    readonly_fields = (
        'student', 'exam', 'session_id', 'total_score', 'max_score',
        'percentage', 'answers_data', 'started_at', 'submitted_at',
        'graded_at', 'grading_method', 'created_at'
    )
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('student', 'exam', 'session_id', 'status')
        }),
        ('Scores', {
            'fields': ('total_score', 'max_score', 'percentage')
        }),
        ('Answers', {
            'fields': ('answers_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'submitted_at', 'graded_at', 'grading_method', 'created_at')
        }),
    )
