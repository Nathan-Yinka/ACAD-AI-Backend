"""URL configuration for the grading app."""
from django.urls import path
from .views import (
    GradeHistoryListView,
    GradeHistoryDetailView,
    AdminExamSessionsListView,
    AdminSessionDetailView,
    AdminExamGradesListView,
    AdminGradeDetailView,
    AdminAllGradesListView,
)

app_name = 'grading'

urlpatterns = [
    # Student endpoints (only scores)
    path('history', GradeHistoryListView.as_view(), name='history-list'),
    path('history/<int:pk>', GradeHistoryDetailView.as_view(), name='history-detail'),
    
    # Admin endpoints (full details)
    path('admin/grades', AdminAllGradesListView.as_view(), name='admin-grades-list'),
    path('admin/grades/<int:pk>', AdminGradeDetailView.as_view(), name='admin-grade-detail'),
    path('admin/exams/<int:exam_id>/sessions', AdminExamSessionsListView.as_view(), name='admin-exam-sessions'),
    path('admin/exams/<int:exam_id>/grades', AdminExamGradesListView.as_view(), name='admin-exam-grades'),
    path('admin/sessions/<int:pk>', AdminSessionDetailView.as_view(), name='admin-session-detail'),
]
