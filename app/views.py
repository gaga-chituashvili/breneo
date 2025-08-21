from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Assessment, Badge, Question, AssessmentSession
from .serializers import AssessmentSerializer, BadgeSerializer, QuestionSerializer
from django.contrib.auth.models import User
from django.utils import timezone
import os, requests, re
import random

# ---------------- Home ----------------
def home(request):
    return HttpResponse("Welcome to Breneo Student Dashboard!")

# ---------------- Dashboard API ----------------
class DashboardProgressAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = User.objects.first()
        if not user:
            return Response({"error": "No demo user"}, status=404)

        assessments = Assessment.objects.filter(user=user)
        badges = Badge.objects.filter(user=user)
        completed = assessments.filter(status='completed').count()
        in_progress = assessments.filter(status='in_progress').count()
        current_session = AssessmentSession.objects.filter(user=user, completed=False).first()

        jobs = [
            {"title": "Python Developer", "match": "85%", "skills": ["Python", "Django"]},
            {"title": "Data Analyst", "match": "75%", "skills": ["SQL", "Python"]},
        ]
        courses = [
            {"title": "Advanced Python", "difficulty": "Intermediate", "duration": "4 weeks"},
            {"title": "Django for Beginners", "difficulty": "Easy", "duration": "6 weeks"},
        ]

        return Response({
            "welcome_message": f"Hello, {user.username}!",
            "progress": {
                "completed_assessments": completed,
                "in_progress_assessments": in_progress,
            },
            "metrics": {
                "total_assessments": assessments.count(),
                "total_badges": badges.count(),
            },
            "recommended_jobs": jobs,
            "recommended_courses": courses,
            "current_session_id": current_session.id if current_session else None
        })

# ---------------- Questions API ----------------
class QuestionsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        questions = Question.objects.all()[:50]
        serializer = QuestionSerializer(questions, many=True)
        # return Response({"error": "Access denied"}, status=403)
        return Response(serializer.data)

# ---------------- Recommended Jobs ----------------
class RecommendedJobsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        jobs = [
            {"title": "Python Developer", "match": "85%", "skills": ["Python", "Django"]},
            {"title": "Data Analyst", "match": "75%", "skills": ["SQL", "Python"]},
        ]
        return Response({"recommended_jobs": jobs})

# ---------------- Recommended Courses ----------------
class RecommendedCoursesAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        courses = [
            {"title": "Advanced Python", "difficulty": "Intermediate", "duration": "4 weeks"},
            {"title": "Django for Beginners", "difficulty": "Easy", "duration": "6 weeks"},
        ]
        return Response({"recommended_courses": courses})

# ---------------- Progress Metrics ----------------
class ProgressMetricsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = User.objects.first()
        if not user:
            return Response({"error": "No demo user"}, status=404)

        assessments = Assessment.objects.filter(user=user)
        badges = Badge.objects.filter(user=user)

        return Response({
            "total_assessments": assessments.count(),
            "completed_assessments": assessments.filter(status='completed').count(),
            "in_progress_assessments": assessments.filter(status='in_progress').count(),
            "total_badges": badges.count()
        })

# ---------------- AI Question Generation ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_ai_question(domain="Python", difficulty="Easy"):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Generate a {difficulty} multiple choice question about {domain}. "
                        "Return in format: Question text\\nOption1\\nOption2\\nOption3\\nOption4\\nCorrect option number (1-4)"
                    )
                }
            ],
            "max_tokens": 300
        }

        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"]
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if len(lines) < 6:
            return None

        correct_option = re.search(r"\d", lines[5])
        if not correct_option:
            return None

        return {
            "text": lines[0],
            "option1": lines[1],
            "option2": lines[2],
            "option3": lines[3],
            "option4": lines[4],
            "correct_option": int(correct_option.group())
        }

    except Exception:
        return None

# ---------------- Start Assessment API ----------------
class StartAssessmentAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = User.objects.first()
        if not user:
            user = User.objects.create(username="demo_user")

        num_questions = int(request.data.get("num_questions", 5))
        questions = list(Question.objects.all())
        if not questions:
            return Response({"error": "No questions available"}, status=400)

        if len(questions) < num_questions:
            num_questions = len(questions)

        selected_questions = random.sample(questions, num_questions)

        session = AssessmentSession.objects.create(
            user=user,
            questions=[{
                "text": q.text,
                "option1": q.option1,
                "option2": q.option2,
                "option3": q.option3,
                "option4": q.option4,
                "correct_option": q.correct_option
            } for q in selected_questions],
            current_question_index=0,
            answers=[]
        )

        return Response({
            "message": "Assessment started",
            "session_id": session.id,
            "questions": session.questions
        })

# ---------------- Submit Answer API ----------------
class SubmitAnswerAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        session_id = request.data.get("session_id")
        answer = request.data.get("answer")
        question_text = request.data.get("question_text")

        if not session_id:
            return Response({"error": "Session ID missing"}, status=400)

        try:
            session = AssessmentSession.objects.get(id=session_id)
        except AssessmentSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        # პასუხის შენახვა
        session.answers.append({
            "question": question_text,
            "answer": answer
        })

        session.current_question_index += 1

        # თუ დასრულდა Assessment
        if session.current_question_index >= len(session.questions):
            session.completed = True
            session.end_time = timezone.now()
            session.save()
            return Response({"message": "Assessment completed"}, status=200)

        next_question = session.questions[session.current_question_index]
        session.save()
        return Response({"next_question": next_question})



class SubmitAnswerAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        session_id = request.data.get("session_id")
        answer = request.data.get("answer")
        question_text = request.data.get("question_text")

        if not session_id:
            return Response({"error": "Session ID missing"}, status=400)

        try:
            session = AssessmentSession.objects.get(id=session_id)
        except AssessmentSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        # მიმდინარე კითხვა
        current_index = session.current_question_index
        question = session.questions[current_index]

        # AI პროგნოზი
        predicted = predict_answer(question['domain'], question['difficulty'])

        # პასუხის შენახვა
        session.answers.append({
            "question": question_text,
            "answer": answer,
            "predicted_correct": predicted
        })

        session.current_question_index += 1

        # თუ დასრულდა Assessment
        if session.current_question_index >= len(session.questions):
            session.completed = True
            session.end_time = timezone.now()
            session.save()
            return Response({"message": "Assessment completed"}, status=200)

        next_question = session.questions[session.current_question_index]
        session.save()
        return Response({"next_question": next_question})