from django.urls import path
from .views import (
    home, DashboardProgressAPI, StartAssessmentAPI,
    ProgressMetricsAPI,SubmitAnswerAPI,CareerPathAPI,DynamictestquestionsAPI,finish_assessment,RecommendedJobsAPI,RecommendedCoursesAPI
)

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/', DashboardProgressAPI.as_view(), name='dashboard-api'),
    path('api/start-assessment/', StartAssessmentAPI.as_view(), name='start-assessment'),
    path('api/jobs/recommended/', RecommendedJobsAPI.as_view(), name='recommended-jobs'),
    path('api/courses/recommended/', RecommendedCoursesAPI.as_view(), name='recommended-courses'),
    path('api/progress/', ProgressMetricsAPI.as_view(), name='progress-metrics'),
    path('api/submit-answer/', SubmitAnswerAPI.as_view(), name='submit-answer'),
    path('api/career-path/', CareerPathAPI.as_view(), name='career-path'),
    path('api/techquestions/', DynamictestquestionsAPI.as_view(), name='tech_questions'),
    path("api/finish-assessment/", finish_assessment, name='finish_assessment'),
]
