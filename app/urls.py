from django.urls import path
from .views import (
    DashboardProgressAPI, QuestionsAPI, StartAssessmentAPI,
    SkillPathAPI, RecommendedJobsAPI, RecommendedCoursesAPI, ProgressMetricsAPI,
    proxy_dashboard, home
)

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/', DashboardProgressAPI.as_view(), name='dashboard-api'),
    path('api/questions/', QuestionsAPI.as_view(), name='questions-api'),
    path('api/start-assessment/', StartAssessmentAPI.as_view(), name='start-assessment'),
    path('api/skill-path/', SkillPathAPI.as_view(), name='skill-path'),
    path('api/jobs/recommended/', RecommendedJobsAPI.as_view(), name='recommended-jobs'),
    path('api/courses/recommended/', RecommendedCoursesAPI.as_view(), name='recommended-courses'),
    path('api/progress/', ProgressMetricsAPI.as_view(), name='progress-metrics'),
    path('api/proxy/', proxy_dashboard, name='proxy-dashboard'),
]