"""
URL configuration for acad_ai_assessment project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.assessments.urls')),
    path('api/v1/grades/', include('apps.grading.urls')),
]

