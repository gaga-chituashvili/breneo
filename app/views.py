from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Assessment, Badge, Question, AssessmentSession
from .serializers import AssessmentSerializer, BadgeSerializer, QuestionSerializer
from django.contrib.auth.models import User
import os, requests

# Home page
def home(request):
    return HttpResponse("Welcome to Breneo Student Dashboard!")

# ---------------- Dashboard API ----------------
class DashboardProgressAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        assessments = Assessment.objects.filter(user=user)
        badges = Badge.objects.filter(user=user)
        completed = assessments.filter(status='completed').count()
        in_progress = assessments.filter(status='in_progress').count()

        return Response({
            'assessments': AssessmentSerializer(assessments, many=True).data,
            'badges': BadgeSerializer(badges, many=True).data,
            'completed_assessments': completed,
            'in_progress_assessments': in_progress
        })

# ---------------- Questions API ----------------
class QuestionsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        questions = Question.objects.all()[:5]
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

# ---------------- Start/Continue Assessment ----------------
class StartAssessmentAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        session = AssessmentSession.objects.filter(user=user, completed=False).first()
        if not session:
            first_question = Question.objects.first()
            if not first_question:
                return Response({"error": "No questions available"}, status=status.HTTP_404_NOT_FOUND)
            session = AssessmentSession.objects.create(user=user, current_question=first_question)

        serializer = QuestionSerializer(session.current_question)
        return Response({
            "message": "Assessment session started" if not session.completed else "Continuing assessment",
            "session_id": session.id,
            "current_question": serializer.data
        })

# ---------------- Skill Path API ----------------
class SkillPathAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        assessments = Assessment.objects.filter(user=user)
        skill_path = [{"name": a.name, "status": a.status, "completed_at": a.completed_at} for a in assessments]

        return Response({"skill_path": skill_path})

# ---------------- Recommended Jobs API ----------------
class RecommendedJobsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        jobs = [
            {"title": "Python Developer", "match": "85%", "skills": ["Python", "Django"]},
            {"title": "Data Analyst", "match": "75%", "skills": ["SQL", "Python"]},
        ]
        return Response({"recommended_jobs": jobs})

# ---------------- Recommended Courses API ----------------
class RecommendedCoursesAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        courses = [
            {"title": "Advanced Python", "difficulty": "Intermediate", "duration": "4 weeks"},
            {"title": "Django for Beginners", "difficulty": "Easy", "duration": "6 weeks"},
        ]
        return Response({"recommended_courses": courses})

# ---------------- Progress Metrics API ----------------
class ProgressMetricsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        assessments = Assessment.objects.filter(user=user)
        badges = Badge.objects.filter(user=user)

        return Response({
            "total_assessments": assessments.count(),
            "completed_assessments": assessments.filter(status='completed').count(),
            "in_progress_assessments": assessments.filter(status='in_progress').count(),
            "total_badges": badges.count()
        })

# ---------------- Proxy API (optional) ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@api_view(['GET'])
def proxy_dashboard(request):
    if not GROQ_API_KEY:
        return Response({"error": "GROQ_API_KEY not set"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    api_url = "https://api.yourservice.com/dashboard/" 
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        r.raise_for_status()
        return Response(r.json())
    except requests.exceptions.RequestException as e:
        return Response({"error": "Failed to fetch dashboard data", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
