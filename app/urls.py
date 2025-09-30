from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    home, DashboardProgressAPI, StartAssessmentAPI,
    ProgressMetricsAPI, SubmitAnswerAPI, CareerPathAPI,
    DynamictestquestionsAPI, finish_assessment, RecommendedJobsAPI,
    RecommendedCoursesAPI, FinishAssessmentAPI, CareerCategoryListAPIView,
    RandomCareerQuestionsAPI, DynamicSoftSkillsquestionsAPI,
    StartSoftAssessmentAPI, SubmitSoftAnswerAPI, FinishSoftAssessmentAPI,
    CareerRoadmapAPI, save_test_results, get_user_results,
    RegisterView, ProfileView ,CustomTokenObtainPairView 
)

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/', DashboardProgressAPI.as_view(), name='dashboard-api'),
    path('api/start-assessment/', StartAssessmentAPI.as_view(), name='start-assessment'),
    path('api/jobs/recommended/', RecommendedJobsAPI.as_view(), name='recommended-jobs'),
    path('api/courses/recommended/', RecommendedCoursesAPI.as_view(), name='recommended-courses'),
    path('api/progress/', ProgressMetricsAPI.as_view(), name='progress-metrics'),
    path('api/submit-answer/', SubmitAnswerAPI.as_view(), name='submit-answer'),
    path('api/careerpath/', CareerPathAPI.as_view(), name='career-path'),
    path('api/techquestions/', DynamictestquestionsAPI.as_view(), name='tech_questions'),
    path("api/finish-assessment-simple/", finish_assessment, name="finish-assessment-simple"),
    path("api/finish-assessment/", FinishAssessmentAPI.as_view(), name="finish-assessment"),
    path('api/career-categories/', CareerCategoryListAPIView.as_view(), name='career-categories'),
    path("api/career-questions-random/", RandomCareerQuestionsAPI.as_view(), name="career-questions-random"),

    # ---------------- Soft Skills Assessment ----------------
    path('api/softskillsquestions/', DynamicSoftSkillsquestionsAPI.as_view(), name='SoftSkills_questions'),
    path("api/soft/start/", StartSoftAssessmentAPI.as_view(), name="start-soft-assessment"),
    path("api/soft/submit/", SubmitSoftAnswerAPI.as_view(), name="submit-soft-answer"),
    path("api/soft/finish/", FinishSoftAssessmentAPI.as_view(), name="finish-soft-assessment"),
    path("api/career-roadmap/", CareerRoadmapAPI.as_view(), name="career-roadmap"),
    path('api/skilltest/save/', save_test_results, name='save_test_results'),
    path('api/skilltest/results/', get_user_results, name='get_user_results'),

    # ---------------- Authentication ----------------
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("api/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api/profile/", ProfileView.as_view(), name="profile"),
]
