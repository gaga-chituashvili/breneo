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
    RegisterView, ProfileView ,CustomTokenObtainPairView,TemporaryAcademyRegisterView,TemporaryAcademyVerifyView,VerifyCodeView,PasswordResetRequestView, PasswordResetVerifyView, SetNewPasswordView
    
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/', DashboardProgressAPI.as_view(), name='dashboard-api'),
    path('api/jobs/recommended/', RecommendedJobsAPI.as_view(), name='recommended-jobs'),
    path('api/courses/recommended/', RecommendedCoursesAPI.as_view(), name='recommended-courses'),
    path('api/start-assessment/', StartAssessmentAPI.as_view(), name='start-assessment'),
    path('api/submit-answer/', SubmitAnswerAPI.as_view(), name='submit-answer'),
    path("api/finish-assessment/", FinishAssessmentAPI.as_view(), name="finish-assessment"),
    path('api/progress/', ProgressMetricsAPI.as_view(), name='progress-metrics'),
    path('api/careerpath/', CareerPathAPI.as_view(), name='career-path'),
    path('api/techquestions/', DynamictestquestionsAPI.as_view(), name='tech_questions'),
    path("api/finish-assessment-simple/", finish_assessment, name="finish-assessment-simple"),
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
    path("api/academy/register/", TemporaryAcademyRegisterView.as_view(), name="academy-register"),
    path("api/verify-code/", VerifyCodeView.as_view(), name="verify-code"),
    path('api/verify-academy-email/', TemporaryAcademyVerifyView.as_view(),name='verify-academy-email'),

    #------------- recovery password ---------------
    path('password-reset/request/', PasswordResetRequestView.as_view()),
    path('password-reset/verify/', PasswordResetVerifyView.as_view()),
    path('password-reset/set-new/', SetNewPasswordView.as_view()),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

