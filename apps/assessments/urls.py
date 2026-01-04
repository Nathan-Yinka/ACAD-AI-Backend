"""URL configuration for the assessments app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExamViewSet,
    AdminExamViewSet,
    AdminQuestionViewSet,
    SessionQuestionView,
    SessionAnswerView,
    SessionProgressView,
    SessionSubmitView,
)

app_name = 'assessments'

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')

admin_router = DefaultRouter()
admin_router.register(r'exams', AdminExamViewSet, basename='admin-exam')
admin_router.register(
    r'exams/(?P<exam_pk>\d+)/questions',
    AdminQuestionViewSet,
    basename='admin-question'
)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
    
    # Session endpoints using token-based tracking
    path('sessions/<str:token>/questions/<int:order>/', SessionQuestionView.as_view(), name='session-question'),
    path('sessions/<str:token>/questions/<int:order>/answer/', SessionAnswerView.as_view(), name='session-answer'),
    path('sessions/<str:token>/progress/', SessionProgressView.as_view(), name='session-progress'),
    path('sessions/<str:token>/submit/', SessionSubmitView.as_view(), name='session-submit'),
]

