from django.urls import path
from .views import (
    home, DashboardProgressAPI, StartAssessmentAPI,
    ProgressMetricsAPI, SubmitAnswerAPI, CareerPathAPI,
    DynamictestquestionsAPI, finish_assessment, RecommendedJobsAPI,
    RecommendedCoursesAPI, FinishAssessmentAPI, CareerCategoryListAPIView,
    RandomCareerQuestionsAPI, DynamicSoftSkillsquestionsAPI,
    StartSoftAssessmentAPI, SubmitSoftAnswerAPI, FinishSoftAssessmentAPI,CareerRoadmapAPI

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
]
