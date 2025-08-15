# ai_app/views.py
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Assessment, Badge, Question, AssessmentSession
from .serializers import AssessmentSerializer, BadgeSerializer, QuestionSerializer
from django.contrib.auth.models import User
import os, requests

# Homepage
def home(request):
    return HttpResponse("Welcome to Breneo Student Dashboard!")

# Dashboard Progress API
class DashboardProgressAPI(APIView):
    authentication_classes = []  # Dev/Test-ისთვის
    permission_classes = []

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            user = User.objects.first()
            if not user:
                return Response({"error": "No users in database"}, status=status.HTTP_404_NOT_FOUND)

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


# AI Questions API
class QuestionsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        questions = Question.objects.all()[:5]
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


# Start / Continue Assessment API
class StartAssessmentAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            user = User.objects.first()  # Dev/Test fallback
            if not user:
                return Response({"error": "No users in database"}, status=status.HTTP_404_NOT_FOUND)

        # ძებნა არსებული session-ისთვის, რომელიც არ არის დასრულებული
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


# Proxy API (GROQ_API_KEY – backend-ში რჩება)
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
        return Response(
            {"error": "Failed to fetch dashboard data", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
