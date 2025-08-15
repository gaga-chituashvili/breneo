from django.urls import path
from .views import DashboardProgressAPI, QuestionsAPI, home, proxy_dashboard, StartAssessmentAPI

urlpatterns = [
    path('', home, name='home'),
    path('api/dashboard/', DashboardProgressAPI.as_view(), name='dashboard-api'),
    path('api/questions/', QuestionsAPI.as_view(), name='questions-api'),
    path('api/proxy/', proxy_dashboard, name='proxy-dashboard'),
    path('api/start-assessment/', StartAssessmentAPI.as_view(), name='start-assessment'),
    
]

