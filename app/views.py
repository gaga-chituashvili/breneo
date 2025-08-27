from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Assessment, Badge, Question, AssessmentSession, UserSkill, Job, Course,DynamicTestQuestion
from .serializers import QuestionSerializer,QuestionTestSerializer
from django.contrib.auth.models import User
from django.utils import timezone
import os, requests, random, re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
        return Response(serializer.data)
    
class DynamictestquestionsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        questions = DynamicTestQuestion.objects.all()[:50]
        serializer = QuestionTestSerializer(questions, many=True)
        return Response(serializer.data)



def get_next_question_domain(answers, previous_domain):
    """
    AI determines next question domain based on user's previous answers.
    """
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        prompt = f"""
        User has answered these questions: {answers}.
        Suggest the next question domain for this user.
        Prefer switching topic if user shows strength in previous domain {previous_domain}.
        Give only a single word domain.
        """
        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10
        }
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        return content or previous_domain
    except Exception:
        return previous_domain

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
                "correct_option": q.correct_option,
                "domain": q.domain,
                "difficulty": q.difficulty
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

        # Save current answer
        session.answers.append({
            "question": question_text,
            "answer": answer
        })
        session.current_question_index += 1
        session.save()

        # Check if assessment completed
        if session.current_question_index >= len(session.questions):
            session.completed = True
            session.end_time = timezone.now()
            session.save()
            return Response({"message": "Assessment completed"}, status=200)

        # Return next question
        next_question = session.questions[session.current_question_index]
        return Response({"next_question": next_question})


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

# ---------------- Career Path API ----------------
def calculate_match(user_skills_qs, job):
    user_skill_names = set(user_skills_qs.values_list("skill__name", flat=True))
    required = set(job.required_skills.values_list("name", flat=True))
    
    overlap = required.intersection(user_skill_names)
    missing = required - user_skill_names
    match_percentage = (len(overlap) / len(required)) * 100 if required else 0

    return {
        "job_title": job.title,
        "description": job.description,
        "match_percentage": round(match_percentage, 2),
        "have_skills": list(overlap),
        "missing_skills": list(missing),
        "salary_range": f"${job.salary_min:,} - ${job.salary_max:,}",
        "time_to_ready": job.time_to_ready,
    }

class CareerPathAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user_obj = User.objects.first()
        if not user_obj:
            return Response({"error": "No demo user"}, status=404)

        user_skills_qs = UserSkill.objects.filter(user=user_obj)
        results = []

        for job in Job.objects.all():
            match_data = calculate_match(user_skills_qs, job)
            # recommended courses
            missing = match_data["missing_skills"]
            rec_courses = Course.objects.filter(skills_taught__name__in=missing).values_list("title", flat=True)
            match_data["recommended_courses"] = list(rec_courses)
            results.append(match_data)

        return Response(results)
