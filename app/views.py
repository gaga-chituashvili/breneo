import joblib
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Assessment, Badge, AssessmentSession, UserSkill, Job, Course, DynamicTechQuestion,Skill
from .serializers import QuestionTechSerializer
from django.contrib.auth.models import User
import os, requests, random
from rest_framework import status


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

        # Assessments & Sessions
        assessments = Assessment.objects.filter(user=user)
        badges = Badge.objects.filter(user=user)
        completed_count = assessments.filter(status='completed').count()
        in_progress_count = assessments.filter(status='in_progress').count()
        current_session = AssessmentSession.objects.filter(user=user, completed=False).first()

        # User skills
        user_skills = UserSkill.objects.filter(user=user)
        skill_summary = {us.skill.name: us.level for us in user_skills}

        # Recommended jobs (dynamic match)
        jobs_data = []
        for job in Job.objects.all():
            match = calculate_match(user_skills, job)
            jobs_data.append(match)

        # Recommended courses (based on missing skills)
        courses_data = []
        for job_match in jobs_data:
            missing_skills = job_match.get("missing_skills", [])
            courses = Course.objects.filter(skills_taught__name__in=missing_skills).values_list("title", flat=True)
            courses_data.extend(list(courses))
        courses_data = list(set(courses_data)) 

        return Response({
            "user": {
                "username": user.username,
                "skills": skill_summary
            },
            "progress": {
                "total_assessments": assessments.count(),
                "completed_assessments": completed_count,
                "in_progress_assessments": in_progress_count,
                "total_badges": badges.count(),
            },
            "current_session": {
                "id": current_session.id if current_session else None,
                "questions_count": len(current_session.questions) if current_session else 0
            },
            "recommended_jobs": jobs_data,
            "recommended_courses": courses_data
        })

# ---------------- Recommended Jobs ----------------
class RecommendedJobsAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = User.objects.first()
        if not user:
            return Response({"error": "No demo user"}, status=404)

        user_skills = UserSkill.objects.filter(user=user)
        jobs_data = [calculate_match(user_skills, job) for job in Job.objects.all()]
        return Response({"recommended_jobs": jobs_data})

# ---------------- Recommended Courses API ----------------
class RecommendedCoursesAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = User.objects.first()
        if not user:
            return Response({"error": "No demo user"}, status=404)

        user_skills = UserSkill.objects.filter(user=user)
        courses_set = set()
        for job in Job.objects.all():
            match_data = calculate_match(user_skills, job)
            missing = match_data.get("missing_skills", [])
            courses = Course.objects.filter(skills_taught__name__in=missing).values_list("title", flat=True)
            courses_set.update(courses)

        return Response({"recommended_courses": list(courses_set)})

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


import os
import joblib
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from app.models import UserSkill, Job, Course

class CareerPathAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        import os, joblib

       
        user = User.objects.first()
        if not user:
            return Response({"error": "No demo user"}, status=404)

        
        model_path = os.path.join("app", "ml", "model.pkl")
        if not os.path.exists(model_path):
            return Response({"error": "ML model not found"}, status=500)
        model = joblib.load(model_path)

        
        user_skills_qs = UserSkill.objects.filter(user=user)
        if not user_skills_qs.exists():
            return Response({"error": "User has no skills"}, status=400)

       
        feature_names = model.feature_names_in_
        skill_vector = [
            user_skills_qs.filter(skill__name=skill).first().points if user_skills_qs.filter(skill__name=skill).exists() else 0
            for skill in feature_names
        ]

        
        try:
            predicted_job_title = model.predict([skill_vector])[0]
        except Exception as e:
            return Response({"error": f"Prediction failed: {str(e)}"}, status=500)

       
        job_title_map = {
            "Backend Developer": "Python Developer",  
            "Frontend Developer": "Frontend Developer",
            "Data Analyst": "Data Analyst",
        }
        db_job_title = job_title_map.get(predicted_job_title, predicted_job_title)

       
        try:
            recommended_job = Job.objects.get(title=db_job_title)
        except Job.DoesNotExist:
            return Response({"error": f"Job '{db_job_title}' not found in DB"}, status=404)

       
        user_skill_names = set(user_skills_qs.values_list("skill__name", flat=True))
        required_skills = set(recommended_job.required_skills.values_list("name", flat=True))
        missing_skills = required_skills - user_skill_names
        rec_courses = Course.objects.filter(skills_taught__name__in=missing_skills).values_list("title", flat=True)

        
        result = {
            "job_title": recommended_job.title,
            "description": recommended_job.description,
            "salary_range": f"${recommended_job.salary_min:,} - ${recommended_job.salary_max:,}",
            "time_to_ready": recommended_job.time_to_ready,
            "missing_skills": list(missing_skills),
            "recommended_courses": list(rec_courses)
        }

        return Response(result)
# ---------------- Questions API ----------------
class DynamictestquestionsAPI(APIView):
    def get(self, request):
        questions = list(DynamicTechQuestion.objects.filter(isactive=True))
        random.shuffle(questions)
        serializer = QuestionTechSerializer(questions, many=True)
        return Response(serializer.data)

# ---------------- AI Next Question Helper ----------------
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
        resp = requests.post(url, headers=headers, json=data, timeout=10)
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
        questions = list(DynamicTechQuestion.objects.filter(isactive=True))
        if not questions:
            return Response({"error": "No questions available"}, status=400)

        if len(questions) < num_questions:
            num_questions = len(questions)

        selected_questions = random.sample(questions, num_questions)

        session = AssessmentSession.objects.create(
            user=user,
            questions=[{
                "text": q.questiontext,
                "option1": q.option1,
                "option2": q.option2,
                "option3": q.option3,
                "option4": q.option4,
                "correct_option": q.correct_option,
                "skill": q.skill,
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
from .views import get_next_question_domain  # იქიდან სადაც გაქვს ეს helper

class SubmitAnswerAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            answer = request.data.get("answer")
            question_text = request.data.get("question_text")

            if not session_id or not answer or not question_text:
                return Response({"error": "Missing parameters"}, status=400)

            session = AssessmentSession.objects.get(id=session_id)

            prev_question = next((q for q in session.questions if q.get("text") == question_text), None)
            if not prev_question:
                return Response({"error": "Question not found in session"}, status=400)

            # ------------------ check correctness ------------------
            is_correct = False
            for i in range(1, 9):
                if answer.strip() == prev_question.get(f"option{i}"):
                    is_correct = (i == prev_question.get("correct_option"))
                    break

            # ------------------ save answer ------------------
            session.answers.append({
                "questiontext": question_text,
                "answer": answer,
                "correct": is_correct,
                "difficulty": prev_question.get("difficulty"),
                "skill": prev_question.get("skill"),
                "RoleMapping": prev_question.get("RoleMapping"),
            })

            # ------------------ AI logic for next domain ------------------
            answers_summary = [
                {"q": a["questiontext"], "ans": a["answer"], "correct": a["correct"]}
                for a in session.answers
            ]
            previous_domain = prev_question.get("RoleMapping")
            next_domain = get_next_question_domain(answers_summary, previous_domain)

            # ------------------ next difficulty ------------------
            if is_correct:
                next_difficulty = (
                    "medium" if prev_question.get("difficulty") == "easy" else
                    "hard" if prev_question.get("difficulty") == "medium" else None
                )
            else:
                next_difficulty = "easy"  # თუ ვერ უპასუხა → დავაბრუნოთ უფრო მარტივზე

            # ------------------ next question selection ------------------
            next_qs = DynamicTechQuestion.objects.filter(
                RoleMapping=next_domain,
                difficulty=next_difficulty if next_difficulty else prev_question.get("difficulty"),
                isactive=True
            )

            if not next_qs.exists():
                next_qs = DynamicTechQuestion.objects.filter(isactive=True)

            next_question = None
            if next_qs.exists():
                nq = random.choice(list(next_qs))
                next_question = {
                    "text": nq.questiontext,
                    "option1": nq.option1,
                    "option2": nq.option2,
                    "option3": nq.option3,
                    "option4": nq.option4,
                    "correct_option": nq.correct_option,
                    "skill": nq.skill,
                    "difficulty": nq.difficulty,
                    "RoleMapping": nq.RoleMapping,
                }
                session.questions.append(next_question)

            session.current_question_index += 1
            session.save()

            return Response({
                "message": "Answer submitted",
                "correct": is_correct,
                "next_question": next_question
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

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



# ---------------- Finish Assessment ----------------
@api_view(["POST"])
def finish_assessment(request):
    session_id = request.data.get("session_id")
    try:
        session = AssessmentSession.objects.get(id=session_id)
    except AssessmentSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    score = 0
    for ans in session.answers:
        try:
            q = DynamicTechQuestion.objects.get(questiontext=ans["questiontext"])
            if q.correct_option and ans["answer"] == getattr(q, f"option{q.correct_option}"):
                score += 1
        except DynamicTechQuestion.DoesNotExist:
            continue

    session.completed = True
    session.save()

    percentage = round((score / len(session.answers)) * 100, 2) if session.answers else 0

    return Response({
        "score": f"{score} / {len(session.answers)}",
        "percentage": percentage
    })



class FinishAssessmentAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response({"error": "Missing session_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = AssessmentSession.objects.get(id=session_id)
        except AssessmentSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        # Initialize skill scores
        skill_scores = {}

        for ans in session.answers:
            question_text = ans.get("questiontext")
            user_answer = ans.get("answer")

            try:
                question = DynamicTechQuestion.objects.get(questiontext=question_text)
            except DynamicTechQuestion.DoesNotExist:
                continue

            skill_name = question.skill
            correct_option = question.correct_option
            correct_answer = getattr(question, f"option{correct_option}")

            # Initialize score for this skill
            if skill_name not in skill_scores:
                skill_scores[skill_name] = 0

            if user_answer.strip() == correct_answer.strip():
                skill_scores[skill_name] += 1

        # Update UserSkill table
        user = session.user
        for skill_name, points in skill_scores.items():
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            user_skill, created = UserSkill.objects.get_or_create(user=user, skill=skill)
            user_skill.points += points
            user_skill.save()

        # Mark session completed
        session.completed = True
        session.save()

        total_score = sum(skill_scores.values())
        total_questions = len(session.answers)

        return Response({
            "message": "Assessment finished successfully",
            "total_score": total_score,
            "total_questions": total_questions,
            "score_per_skill": skill_scores,
        })
