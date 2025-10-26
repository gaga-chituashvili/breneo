import joblib
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from .models import Assessment, Badge, AssessmentSession, UserSkill, Job, Course, DynamicTechQuestion,Skill,CareerCategory,DynamicSoftSkillsQuestion,SkillScore,SkillTestResult,TemporaryUser, UserProfile,PasswordResetCode,SocialLinks
from .serializers import QuestionTechSerializer,CareerCategorySerializer,QuestionSoftSkillsSerializer,CustomTokenObtainPairSerializer,SkillTestResultSerializer,RegisterSerializer,TemporaryAcademyRegisterSerializer,UserProfileUpdateSerializer, AcademyUpdateSerializer,AcademyChangePasswordSerializer,SocialLinksSerializer
from django.contrib.auth.models import User
import os, requests, random
from rest_framework import status
from rest_framework import generics
from .models import CareerQuestion,Academy,UserProfile,TemporaryAcademy
from .serializers import CareerQuestionSerializer,UserProfileSerializer
import json
import json
import joblib
import pandas as pd
from groq import Groq
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
import time
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework.parsers import JSONParser, FormParser,MultiPartParser
from random import randint
from .serializers import (
    PasswordResetRequestSerializer, 
    PasswordResetVerifySerializer, 
    SetNewPasswordSerializer
)
from django.contrib.auth import get_user_model





GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------- Home ----------------
def home(request):
    return HttpResponse("Welcome to Breneo Student Dashboard!")

# ---------------- Dashboard API ----------------
class DashboardProgressAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
            return Response({"error": "No demo user"}, status=404)

        # 🟢 Use saved skill test results
        results = SkillTestResult.objects.filter(user=user).order_by('-created_at')
        last_result = results.first()

        skill_summary = last_result.skills_json if last_result else {}
        final_role = last_result.final_role if last_result else None

        # Assessments & Badges
        badges = Badge.objects.filter(user=user)

        return Response({
            "user": {"username": user.username, "skills": skill_summary},
            "progress": {
                "total_tests": results.count(),
                "last_total_score": last_result.total_score if last_result else None,
                "total_badges": badges.count(),
            },
            "last_result": {
                "final_role": final_role,
                "total_score": last_result.total_score if last_result else None,
            }
        })

# ---------------- Recommended Jobs ----------------

class RecommendedJobsAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
            return Response({"error": "No demo user"}, status=404)

        # 🟢 Use last SkillTestResult
        last_result = SkillTestResult.objects.filter(user=user).order_by('-created_at').first()
        if not last_result or not last_result.final_role:
            return Response({"error": "No completed skill test found"}, status=400)

        final_role = last_result.final_role
        skills_json = last_result.skills_json

        # Convert skills_json to queryset-like list for calculate_match()
        user_skills = []
        for skill_name, status in skills_json.items():
            skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
            points = 1 if status.lower() == "strong" else 0
            user_skills.append(UserSkill(user=user, skill=skill_obj, points=points))

        jobs_data = []
        jobs_qs = Job.objects.filter(role__iexact=final_role)
        if not jobs_qs.exists():
            jobs_qs = Job.objects.all()

        for job in jobs_qs:
            try:
                match_data = calculate_match(user_skills, job)

                # AI Salary Range
                try:
                    ai_salary = fetch_salary_from_groq(job.title, location="Georgia")
                except Exception:
                    ai_salary = "$0 - $0"

                match_data["ai_salary_range"] = ai_salary
                jobs_data.append(match_data)

            except Exception as e:
                print(f"Error processing job {job.title}: {e}")
                continue

        return Response({
            "final_role": final_role,
            "recommended_jobs": jobs_data
        })

    
# ---------------- Recommended Courses API ----------------
class RecommendedCoursesAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
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


class CareerPathAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user:
            return Response({"error": "No demo user"}, status=404)

        # Load ML model if exists
        model_path = os.path.join("app", "ml", "model.pkl")
        user_skills_qs = UserSkill.objects.filter(user=user)
        skill_vector = {s.skill.name: s.points for s in user_skills_qs}

        predicted_job_title = None
        if os.path.exists(model_path) and skill_vector:
            try:
                clf = joblib.load(model_path)
                X = pd.DataFrame([skill_vector])
                predicted_job_title = clf.predict(X)[0]
            except:
                predicted_job_title = None

        # fallback based on strongest skill
        if not predicted_job_title and skill_vector:
            strongest_skill = max(skill_vector.items(), key=lambda x: x[1])[0].lower()
            role_mapping = {
                        "communication": "Team Player",
                        "teamwork": "Team Player",
                        "adaptability": "Problem Solver",
                        "task management": "Efficient Planner",
                        "time management": "Organized Worker",
                        "leadership": "Leader / Manager",
                        "project management": "Project Manager",
                        "learning ability": "Curious Learner",
                        "react": "Frontend Developer",
                        "vue": "Frontend Developer",
                        "angular": "Frontend Developer",
                        "javascript": "Frontend Developer",
                        "typescript": "Frontend Developer",
                        "ios": "iOS Developer",
                        "android": "Android Developer",
                        "react native": "React Native Developer",
                        "ui/ux": "UI/UX Designer",
                        "graphic designer": "Graphic Designer",
                        "3d modeler": "3D Modeler",
                        "product designer": "Product Designer",
                        "python": "Backend Developer",
                        "django": "Backend Developer",
                        "flask": "Backend Developer",
                        "node.js": "Backend Developer",
                        "express.js": "Backend Developer",
                        "sql": "Data Analyst",
                        "mongodb": "Data Analyst",
                        "data analyst": "Data Analyst",
                        "content creator": "Content Creator",
                        "video editor": "Content Creator",
                        "copywriter": "Content Creator",
                        "devops": "DevOps Engineer",
                        "aws": "DevOps Engineer",
                        "docker": "DevOps Engineer",
                        "kubernetes": "DevOps Engineer"
                    }
            predicted_job_title = role_mapping.get(strongest_skill, "N/A")

        try:
            job_obj = Job.objects.get(title=predicted_job_title)
        except Job.DoesNotExist:
            return Response({"error": f"Job '{predicted_job_title}' not found"}, status=404)

        user_skills = set(user_skills_qs.values_list("skill__name", flat=True))
        required_skills = set(job_obj.required_skills.values_list("name", flat=True))
        missing_skills = required_skills - user_skills
        rec_courses = Course.objects.filter(skills_taught__name__in=missing_skills).values_list("title", flat=True)

        return Response({
            "job_title": job_obj.title,
            "description": job_obj.description,
            "salary_range": f"${job_obj.salary_min:,} - ${job_obj.salary_max:,}",
            "time_to_ready": job_obj.time_to_ready,
            "missing_skills": list(missing_skills),
            "recommended_courses": list(rec_courses)
        })

# ---------------- Questions API ----------------

class DynamictestquestionsAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = list(DynamicTechQuestion.objects.filter(isactive=True))
        random.shuffle(questions)
        serializer = QuestionTechSerializer(questions, many=True)
        return Response(serializer.data)
    

class DynamicSoftSkillsquestionsAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = list(DynamicSoftSkillsQuestion.objects.filter(isactive=True))
        random.shuffle(questions)
        serializer = QuestionSoftSkillsSerializer(questions, many=True)
        return Response(serializer.data)





class CareerCategoryListAPIView(generics.ListAPIView):
    queryset = CareerCategory.objects.all()
    serializer_class = CareerCategorySerializer
    authentication_classes = [JWTAuthentication]

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        role_mapping = request.data.get("RoleMapping")
        num_questions = int(request.data.get("num_questions", 10))

       
        questions_qs = DynamicTechQuestion.objects.filter(RoleMapping=role_mapping, isactive=True)
        if questions_qs.count() < num_questions:
            questions_qs = DynamicTechQuestion.objects.filter(isactive=True)

        selected_questions = random.sample(list(questions_qs), min(num_questions, questions_qs.count()))

        session = AssessmentSession.objects.create(
            user=user,
            questions=[{
                "text": q.questiontext,
                "option1": q.option1,
                "option2": q.option2,
                "option3": q.option3,
                "option4": q.option4,
                "correct_option": q.correct_option,
                "skill": q.skill.strip(),
                "difficulty": q.difficulty,
                "RoleMapping": q.RoleMapping
            } for q in selected_questions],
            current_question_index=0,
            answers=[]
        )

        return Response({
            "message": "Assessment started",
            "session_id": session.id,
            "questions": session.questions
        })


# ---------------- Submit Answer ----------------
class SubmitAnswerAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                return Response({"error": "Missing session_id"}, status=400)
            session = AssessmentSession.objects.get(id=session_id, user=request.user)
            answer = request.data.get("answer")
            question_text = request.data.get("question_text")

            if not session_id or not answer or not question_text:
                return Response({"error": "Missing parameters"}, status=400)

            session = AssessmentSession.objects.get(id=session_id)

            prev_question = next((q for q in session.questions if q.get("text") == question_text), None)
            if not prev_question:
                return Response({"error": "Question not found in session"}, status=400)

            correct_opt_num = prev_question["correct_option"]
            is_correct = (answer.strip() == prev_question[f"option{correct_opt_num}"].strip())

            prev_skill = (prev_question.get("skill") or "").strip()
            prev_role = prev_question.get("RoleMapping")
            prev_difficulty = prev_question.get("difficulty")

            # Save answer
            session.answers.append({
                "text": question_text,
                "answer": answer,
                "correct": is_correct,
                "difficulty": prev_difficulty,
                "skill": prev_skill,
                "RoleMapping": prev_role,
            })

            
            if is_correct:
                next_skill = prev_skill
                next_difficulty = "hard" if prev_difficulty != "hard" else "hard"
            else:
                next_difficulty = "easy"
                skills_in_role = list(DynamicTechQuestion.objects.filter(
                    RoleMapping=prev_role, isactive=True
                ).values_list("skill", flat=True).distinct())
                skills_in_role = [s.strip() for s in skills_in_role if s]
                prev_skill_norm = prev_skill.lower()
                skills_in_role_norm = [s.lower() for s in skills_in_role]

                available_skills = [
                    skills_in_role[i] for i, s in enumerate(skills_in_role_norm) if s != prev_skill_norm
                ]
                next_skill = random.choice(available_skills) if available_skills else prev_skill

            
            answered_texts = [a["text"] for a in session.answers]
            next_qs = list(DynamicTechQuestion.objects.filter(
                RoleMapping=prev_role,
                skill=next_skill,
                difficulty=next_difficulty,
                isactive=True
            ).exclude(questiontext__in=answered_texts))

            if not next_qs:
               
                next_qs = list(DynamicTechQuestion.objects.filter(
                    RoleMapping=prev_role,
                    isactive=True
                ).exclude(questiontext__in=answered_texts))

            next_question = None
            if next_qs:
                nq = random.choice(next_qs)
                next_question = {
                    "text": nq.questiontext,
                    "option1": nq.option1,
                    "option2": nq.option2,
                    "option3": nq.option3,
                    "option4": nq.option4,
                    "correct_option": nq.correct_option,
                    "skill": nq.skill.strip(),
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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


class FinishAssessmentAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                return Response({"error": "Missing session_id"}, status=400)
            session = AssessmentSession.objects.get(id=session_id, user=request.user)

            # Load answers
            answers = session.answers or []
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except Exception:
                    answers = []

            skill_scores = {}
            skill_totals = {}

            # Calculate per-skill scores
            for ans in answers:
                if not isinstance(ans, dict):
                    continue
                question_text = (ans.get("text") or "").strip()
                user_answer = (ans.get("answer") or "").strip()
                if not question_text or not user_answer:
                    continue

                question = DynamicTechQuestion.objects.filter(questiontext__iexact=question_text).first()
                if not question:
                    continue

                skill_name = (question.skill or "").strip()
                correct_option = getattr(question, "correct_option", None)
                correct_answer = getattr(question, f"option{correct_option}", "").strip() if correct_option else ""

                skill_scores.setdefault(skill_name, 0)
                skill_totals.setdefault(skill_name, 0)
                skill_totals[skill_name] += 1
                if user_answer == correct_answer:
                    skill_scores[skill_name] += 1

            user = session.user
            results = {}
            threshold_strong = 70.0
            threshold_borderline = 60.0

            # Update UserSkill & SkillScore
            for skill_name, correct_count in skill_scores.items():
                total = skill_totals.get(skill_name, 0)
                if total == 0:
                    continue

                percentage = round((correct_count / total) * 100, 2)
                skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
                user_skill, _ = UserSkill.objects.get_or_create(user=user, skill=skill_obj)
                user_skill.points += correct_count
                user_skill.save()

                SkillScore.objects.create(
                    user=user,
                    skill=skill_obj,
                    score=percentage,
                    threshold=threshold_strong
                )

                if percentage >= threshold_strong:
                    rec = "✅ Strong"
                elif percentage >= threshold_borderline:
                    rec = "⚠️ Borderline"
                else:
                    rec = "❌ Weak"

                results[skill_name] = {
                    "score": f"{correct_count}/{total}",
                    "percentage": f"{percentage}%",
                    "recommendation": rec
                }

            total_score = sum(skill_scores.values())
            total_questions = sum(skill_totals.values())
            score_per_skill = {skill: data["percentage"] for skill, data in results.items()}

            session.completed = True
            session.save()

            # ==== ML Prediction ====
            final_role = "N/A"
            try:
                all_skills = list(UserSkill.objects.filter(user=user).values_list("skill__name", flat=True))
                skill_vector = {skill: UserSkill.objects.filter(user=user, skill__name=skill).first().points for skill in all_skills}

                if skill_vector:
                    clf = joblib.load("app/ml/model.pkl")
                    X = pd.DataFrame([skill_vector])
                    predicted_role = clf.predict(X)[0]
                    final_role = predicted_role
            except Exception:
                pass

            # ==== Fallback Role Mapping ====
            if final_role == "N/A" and results:
                strongest_skill = max(results.items(), key=lambda item: float(item[1]['percentage'].replace('%', '')))[0].strip().lower()
                role_mapping = {
                    "react": "Frontend Developer",
                    "vue": "Frontend Developer",
                    "angular": "Frontend Developer",
                    "javascript": "Frontend Developer",
                    "typescript": "Frontend Developer",
                    "ios": "iOS Developer",
                    "android": "Android Developer",
                    "react native": "React Native Developer",
                    "ui/ux": "UI/UX Designer",
                    "graphic designer": "Graphic Designer",
                    "3d modeler": "3D Modeler",
                    "product designer": "Product Designer",
                    "python": "Backend Developer",
                    "django": "Backend Developer",
                    "flask": "Backend Developer",
                    "node.js": "Backend Developer",
                    "express.js": "Backend Developer",
                    "sql": "Data Analyst",
                    "mongodb": "Data Analyst",
                    "data analyst": "Data Analyst",
                    "content creator": "Content Creator",
                    "video editor": "Content Creator",
                    "copywriter": "Content Creator",
                    "devops": "DevOps Engineer",
                    "aws": "DevOps Engineer",
                    "docker": "DevOps Engineer",
                    "kubernetes": "DevOps Engineer",
                    "communication": "Team Player",
                    "teamwork": "Team Player",
                    "adaptability": "Problem Solver",
                    "task management": "Efficient Planner",
                    "time management": "Organized Worker",
                    "leadership": "Leader / Manager",
                    "project management": "Project Manager",
                    "learning ability": "Curious Learner",
                    "Time & Task Management": "Efficient Planner",
                    "Adaptability & Learning": "Proactive Learner",
                    "Communication & Teamwork": "Team Player",
                }
                normalized_role_mapping = {k.lower(): v for k, v in role_mapping.items()}
                final_role = normalized_role_mapping.get(strongest_skill, "N/A")

            return Response({
                "message": "Assessment finished successfully",
                "total_score": total_score,
                "total_questions": total_questions,
                "results": results,
                "score_per_skill": score_per_skill,
                "final_role": final_role
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)



class StartSoftAssessmentAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            num_questions = 10

            questions_qs = list(DynamicSoftSkillsQuestion.objects.filter(isactive=True))
            if not questions_qs:
                return Response({"error": "No soft skills questions available"}, status=400)

            selected_questions = random.sample(questions_qs, min(num_questions, len(questions_qs)))
            random.shuffle(selected_questions)

            session = AssessmentSession.objects.create(
                user=user,
                questions=[{
                    "questiontext": q.questiontext,
                    "option1": q.option1,
                    "option2": q.option2,
                    "option3": q.option3,
                    "option4": q.option4,
                    "correct_option": q.correct_option,
                    "skill": q.skill.strip(),
                    "difficulty": q.difficulty,
                    "RoleMapping": q.RoleMapping,
                    "type": "soft"
                } for q in selected_questions],
                current_question_index=0,
                answers=[]
            )

            first_question = session.questions[0] if session.questions else None

            return Response({
                "message": "Soft assessment started",
                "session_id": session.id,
                "first_question": first_question
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

class SubmitSoftAnswerAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                return Response({"error": "Missing session_id"}, status=400)
            session = AssessmentSession.objects.get(id=session_id, user=request.user)
            answer = request.data.get("answer")
            question_text = request.data.get("question_text")

            if not session_id or not answer or not question_text:
                return Response({"error": "Missing parameters"}, status=400)

            session = AssessmentSession.objects.get(id=session_id)

            session.answers.append({"question_text": question_text, "answer": answer})
            session.current_question_index += 1
            session.save()

            if session.current_question_index >= len(session.questions):
                total_score = sum(
                    1 for q, a in zip(session.questions, session.answers)
                    if a["answer"] == q[f"option{q['correct_option']}"]
                )
                total_questions = len(session.questions)
                session.completed = True
                session.save()

                return Response({
                    "message": "Assessment finished",
                    "total_score": total_score,
                    "total_questions": total_questions
                })

            next_question = session.questions[session.current_question_index]
            return Response({
                "message": "Answer submitted",
                "next_question": next_question
            })

        except AssessmentSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        


class FinishSoftAssessmentAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                return Response({"error": "Missing session_id"}, status=400)

            session = AssessmentSession.objects.get(id=session_id, user=request.user)

            # Load answers safely
            answers = session.answers or []
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except Exception:
                    answers = []

            skill_scores = {}
            skill_totals = {}

            # Calculate per-skill scores
            for ans in answers:
                if not isinstance(ans, dict):
                    continue
                question_text = (ans.get("question_text") or "").strip()
                user_answer = (ans.get("answer") or "").strip()
                if not question_text or not user_answer:
                    continue

                question = DynamicSoftSkillsQuestion.objects.filter(
                    questiontext__iexact=question_text
                ).first()
                if not question:
                    continue

                skill_name = (question.skill or "").strip()
                correct_option = getattr(question, "correct_option", None)
                correct_answer = getattr(question, f"option{correct_option}", "").strip() if correct_option else ""

                skill_scores.setdefault(skill_name, 0)
                skill_totals.setdefault(skill_name, 0)
                skill_totals[skill_name] += 1
                if user_answer == correct_answer:
                    skill_scores[skill_name] += 1

            user = session.user
            results = {}
            threshold_strong = 70.0
            threshold_borderline = 60.0

            # Update UserSkill & SkillScore safely
            for skill_name, correct_count in skill_scores.items():
                total = skill_totals.get(skill_name, 0)
                if total == 0:
                    continue

                percentage = round((correct_count / total) * 100, 2)

                skill_obj, _ = Skill.objects.get_or_create(name=skill_name)

                # ===== SAFETY FIX: avoid MultipleObjectsReturned =====
                user_skill = UserSkill.objects.filter(user=user, skill=skill_obj).first()
                if not user_skill:
                    user_skill = UserSkill.objects.create(user=user, skill=skill_obj, points=0)

                user_skill.points += correct_count
                user_skill.save()

                SkillScore.objects.create(
                    user=user,
                    skill=skill_obj,
                    score=percentage,
                    threshold=threshold_strong
                )

                if percentage >= threshold_strong:
                    rec = "✅ Strong"
                elif percentage >= threshold_borderline:
                    rec = "⚠️ Borderline"
                else:
                    rec = "❌ Weak"

                results[skill_name] = {
                    "score": f"{correct_count}/{total}",
                    "percentage": f"{percentage}%",
                    "recommendation": rec
                }

            total_score = sum(skill_scores.values())
            total_questions = sum(skill_totals.values())
            score_per_skill = {skill: data["percentage"] for skill, data in results.items()}

            # Mark session completed
            session.completed = True
            session.save()

            # ==== ML Prediction ====
            final_role = "N/A"
            try:
                all_skills = list(UserSkill.objects.filter(user=user).values_list("skill__name", flat=True))
                skill_vector = {skill: UserSkill.objects.filter(user=user, skill__name=skill).first().points for skill in all_skills}

                if skill_vector:
                    clf = joblib.load("app/ml/model.pkl") 
                    X = pd.DataFrame([skill_vector])
                    predicted_role = clf.predict(X)[0]
                    final_role = predicted_role
            except Exception:
                pass

            # ==== Fallback Role Mapping ====
            if final_role == "N/A" and results:
                cleaned_results = {k.strip().lower(): v for k, v in results.items()}
                strongest_skill = max(
                    cleaned_results.items(),
                    key=lambda item: float(item[1]['percentage'].replace('%', ''))
                )[0]

                role_mapping = {
                    "communication": "Team Player",
                    "teamwork": "Team Player",
                    "adaptability": "Problem Solver",
                    "task management": "Efficient Planner",
                    "time management": "Organized Worker",
                    "leadership": "Leader / Manager",
                    "project management": "Project Manager",
                    "learning ability": "Curious Learner",
                    "time & task management": "Efficient Planner",
                    "adaptability & learning": "Proactive Learner",
                    "communication & teamwork": "Team Player",
                    "react": "Frontend Developer",
                    "vue": "Frontend Developer",
                    "angular": "Frontend Developer",
                    "javascript": "Frontend Developer",
                    "typescript": "Frontend Developer",
                    "ios": "iOS Developer",
                    "android": "Android Developer",
                    "react native": "React Native Developer",
                    "ui/ux": "UI/UX Designer",
                    "graphic designer": "Graphic Designer",
                    "3d modeler": "3D Modeler",
                    "product designer": "Product Designer",
                    "python": "Backend Developer",
                    "django": "Backend Developer",
                    "flask": "Backend Developer",
                    "node.js": "Backend Developer",
                    "express.js": "Backend Developer",
                    "sql": "Data Analyst",
                    "mongodb": "Data Analyst",
                    "data analyst": "Data Analyst",
                    "content creator": "Content Creator",
                    "video editor": "Content Creator",
                    "copywriter": "Content Creator",
                    "devops": "DevOps Engineer",
                    "aws": "DevOps Engineer",
                    "docker": "DevOps Engineer",
                    "kubernetes": "DevOps Engineer"
                }
                normalized_role_mapping = {k.lower(): v for k, v in role_mapping.items()}
                final_role = normalized_role_mapping.get(strongest_skill, "N/A")

            return Response({
                "message": "Soft Skills Assessment finished successfully",
                "total_score": total_score,
                "total_questions": total_questions,
                "results": results or {},
                "score_per_skill": score_per_skill or {},
                "final_role": final_role
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)




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





class RandomCareerQuestionsAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 5))
            all_questions = list(CareerQuestion.objects.all())
            if not all_questions:
                return Response({"error": "No questions found"}, status=404)

            
            random.shuffle(all_questions)

            
            questions = all_questions[:min(limit, len(all_questions))]

            serializer = CareerQuestionSerializer(questions, many=True)
            data = serializer.data

            
            for q_idx, q in enumerate(questions):
                for o_idx, opt in enumerate(q.options.all()):
                    data[q_idx]['options'][o_idx]['RoleMapping'] = opt.RoleMapping

            return Response(data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        



def get_top_role(answers):
    role_counts = {}
    for a in answers:
        role = a.get("RoleMapping")
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1
    if not role_counts:
        return None
    return max(role_counts, key=role_counts.get)




class CareerRoadmapAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.first()  # demo purposes
        if not user:
            return Response({"error": "No demo user"}, status=404)

        # -------- User Skills Snapshot --------
        user_skills_qs = UserSkill.objects.filter(user=user)
        skill_snapshot = {us.skill.name: us.points for us in user_skills_qs}

        # -------- Career Matches --------
        jobs_data = []
        for job in Job.objects.all():
            match = calculate_match(user_skills_qs, job)

            # Missing skills -> Recommended courses
            missing_skills = match.get("missing_skills", [])
            recommended_courses = Course.objects.filter(
                skills_taught__name__in=missing_skills
            ).values_list("title", flat=True)

            match["recommended_courses"] = list(set(recommended_courses))
            jobs_data.append(match)

        # -------- Identify top career (optional) --------
        top_career = max(jobs_data, key=lambda j: j["match_percentage"]) if jobs_data else None

        return Response({
            "user_skills": skill_snapshot,
            "career_matches": jobs_data,
            "top_career": top_career
        })



def fetch_salary_from_groq(job_title: str, location: str = "global") -> str:
    """
    Ask Groq AI for an estimated salary range for a given job and location.
    Returns a clean string like '$70,000 - $120,000'
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    
    prompt = (
        f"Provide a realistic yearly salary range in USD "
        f"for a {job_title} in {location} with mid-level experience. "
        f"Return ONLY the range like '$70,000 - $120,000'."
    )
    
    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    return chat.choices[0].message.content.strip()




# Save skill test results
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_test_results(request):
    """
    API to save skill test results.
    Expects JSON:
    {
        "final_role": "Developer",
        "obtained_score": 14,
        "total_questions": 25,
        "skills_json": { ... }
    }
    """
    data = request.data.copy()
    # ფორმატირება "14 / 25"
    obtained = data.get("obtained_score", 0)
    total = data.get("total_questions", 0)
    data["total_score"] = f"{obtained} / {total}"

    serializer = SkillTestResultSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
# Get logged-in user's skill test results
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_results(request):
    results = SkillTestResult.objects.filter(user=request.user).order_by('-created_at')
    serializer = SkillTestResultSerializer(results, many=True)
    return Response(serializer.data)

# --------------------------
# User Registration
# --------------------------

class RegisterView(generics.CreateAPIView):
    queryset = TemporaryUser.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request):
        email = request.data.get("email")
        temp_user = TemporaryUser.objects.filter(email=email).first()

        if temp_user:
            temp_user.first_name = request.data.get("first_name")
            temp_user.last_name = request.data.get("last_name")
            temp_user.password = make_password(request.data.get("password"))
            temp_user.phone_number = request.data.get("phone_number")
        else:
            temp_user = TemporaryUser.objects.create(
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                email=email,
                password=make_password(request.data.get("password")),
                phone_number=request.data.get("phone_number"),
            )

        temp_user.generate_verification_code()
        temp_user.save()

        send_mail(
            "Your Verification Code",
            f"Your verification code is: {temp_user.verification_code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )

        return Response({"message": "Verification code sent to your email."}, status=200)




class VerifyCodeView(APIView):
    parser_classes = [JSONParser, FormParser]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "Email and code are required"}, status=status.HTTP_400_BAD_REQUEST)

        # მომხმარებლის ვერიოფიკაცია
        temp_user = TemporaryUser.objects.filter(email=email).first()
        temp_academy = TemporaryAcademy.objects.filter(email=email).first()

        if not temp_user and not temp_academy:
            return Response({"error": "No temporary record found for this email"}, status=status.HTTP_404_NOT_FOUND)

        # თუ არის TemporaryUser
        if temp_user:
            if temp_user.verification_code != code:
                return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)
            if temp_user.code_expires_at < timezone.now():
                temp_user.delete()
                return Response({"error": "Verification code expired"}, status=status.HTTP_400_BAD_REQUEST)
            
            # უკვე არსებობს User
            if User.objects.filter(email=temp_user.email).exists():
                temp_user.delete()
                return Response({"error": "A user with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # User-ის შექმნა
            user = User.objects.create(
                username=temp_user.email,
                first_name=temp_user.first_name,
                last_name=temp_user.last_name,
                email=temp_user.email,
                password=temp_user.password,
                is_active=True
            )
            # UserProfile შექმნა
            UserProfile.objects.create(
                user=user,
                phone_number=temp_user.phone_number
            )
            temp_user.delete()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

        # თუ არის TemporaryAcademy
        if temp_academy:
            if temp_academy.verification_code != code:
                return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)
            if temp_academy.code_expires_at < timezone.now():
                temp_academy.delete()
                return Response({"error": "Verification code expired"}, status=status.HTTP_400_BAD_REQUEST)
            
            # უკვე არსებობს Academy
            if Academy.objects.filter(email=temp_academy.email).exists():
                temp_academy.delete()
                return Response({"error": "An academy with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Academy-ის შექმნა
            academy = Academy.objects.create(
                name=temp_academy.name,
                email=temp_academy.email,
                password=temp_academy.password,
                phone_number=temp_academy.phone_number,
                description=temp_academy.description,
                website=temp_academy.website,
                is_verified=True
            )
            temp_academy.delete()
            return Response({"message": "Academy registered successfully!"}, status=status.HTTP_201_CREATED)

        
        
# --------------------------
# User Profile
# --------------------------


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)
        profile_image_url = None
        phone = None
        if profile:
            phone = profile.phone_number
            if profile.profile_image:
                profile_image_url = request.build_absolute_uri(profile.profile_image.url)

        return Response({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": phone,
            "profile_image": profile_image_url
        })

    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        # reload profile image url
        profile = getattr(user, "profile", None)
        profile_image_url = request.build_absolute_uri(profile.profile_image.url) if profile and profile.profile_image else None

        return Response({
            "message": "Profile updated successfully.",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": profile.phone_number if profile else None,
            "profile_image": profile_image_url
        }, status=status.HTTP_200_OK)


class AcademyProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]  

    def get_academy(self, request):
        if hasattr(request.user, "email"):
            return Academy.objects.filter(email__iexact=request.user.email).first()
        return None

    def get(self, request):
        academy = self.get_academy(request)
        if not academy:
            return Response({"error": "Academy not found or not authenticated as academy."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "name": academy.name,
            "email": academy.email,
            "phone_number": academy.phone_number,
            "description": academy.description,
            "website": academy.website
        })

    def patch(self, request):
        academy = self.get_academy(request)
        if not academy:
            return Response({"error": "Academy not found or not authenticated as academy."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AcademyUpdateSerializer(academy, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response({
            "message": "Academy profile updated successfully.",
            "name": academy.name,
            "email": academy.email,
            "phone_number": academy.phone_number,
            "description": academy.description,
            "website": academy.website
        }, status=status.HTTP_200_OK)


# --------------------------
# Token View
# --------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# --------------------------
# Academy Registration
# --------------------------


class TemporaryAcademyRegisterView(generics.CreateAPIView):
    queryset = TemporaryAcademy.objects.all()
    serializer_class = TemporaryAcademyRegisterSerializer

    def post(self, request):
        email = request.data.get("email")
        temp_academy = TemporaryAcademy.objects.filter(email=email).first()

        if temp_academy:
            temp_academy.name = request.data.get("name")
            temp_academy.password = make_password(request.data.get("password"))
            temp_academy.phone_number = request.data.get("phone_number")
            temp_academy.description = request.data.get("description")
            temp_academy.website = request.data.get("website")
        else:
            temp_academy = TemporaryAcademy.objects.create(
                name=request.data.get("name"),
                email=email,
                password=make_password(request.data.get("password")),
                phone_number=request.data.get("phone_number"),
                description=request.data.get("description"),
                website=request.data.get("website"),
            )

        temp_academy.generate_verification_code()
        temp_academy.save()

        send_mail(
            "Your Academy Verification Code",
            f"Your verification code is: {temp_academy.verification_code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )

        return Response({"message": "Verification code sent to your email."}, status=200)


class TemporaryAcademyVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "Email and code are required"}, status=400)

        try:
            temp_academy = TemporaryAcademy.objects.get(email=email)
        except TemporaryAcademy.DoesNotExist:
            return Response({"error": "Temporary academy not found"}, status=404)

        if temp_academy.verification_code != code:
            return Response({"error": "Invalid verification code"}, status=400)

        if temp_academy.code_expires_at < timezone.now():
            temp_academy.delete()
            return Response({"error": "Verification code expired"}, status=400)

        # აქ ვამოწმებთ უნიკალურობას
        if Academy.objects.filter(email=email).exists():
            temp_academy.delete()
            return Response({"error": "An academy with this email already exists"}, status=400)


        academy = Academy.objects.create(
            name=temp_academy.name,
            email=temp_academy.email,
            password=temp_academy.password,
            phone_number=temp_academy.phone_number,
            description=temp_academy.description,
            website=temp_academy.website,
            is_verified=True
        )

        temp_academy.delete()

        return Response({"message": "Academy registered successfully!"}, status=201)




# --------------------------
# Password Recovery
# --------------------------


class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=400)

        code = f"{randint(100000, 999999)}"
        PasswordResetCode.objects.create(user=user, code=code)

        send_mail(
            subject="Password Reset Code",
            message=f"Your password reset code is: {code}",
            from_email=None, 
            recipient_list=[email],
        )

        return Response({"message": "Password reset code sent to email"})

class PasswordResetVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        try:
            reset_code = PasswordResetCode.objects.get(user=user, code=code)
        except PasswordResetCode.DoesNotExist:
            return Response({"error": "Invalid code"}, status=400)

        if reset_code.is_expired():
            return Response({"error": "Code expired"}, status=400)

        return Response({"message": "Code verified"})

class SetNewPasswordView(APIView):
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(user=user, code=code).last()
            if not reset_code or reset_code.is_expired():
                return Response({"error": "Invalid or expired code"}, status=400)
        except User.DoesNotExist:
            return Response({"error": "Invalid email"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully"})




class UserProfileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)





#----------- User Change Password ----------------

User = get_user_model()
from .serializers import ChangePasswordSerializer

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"message": "Password changed successfully"})
    


#----------------- Academy Change Password ---------------



class AcademyChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AcademyChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            academy = request.user
            academy.password = make_password(serializer.validated_data['new_password'])
            academy.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





#----------------- Photo Upload ---------------

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        profile = request.user.profile
        if profile.profile_image:
            profile.profile_image.delete(save=True)
            profile.profile_image = None
            profile.save()
            return Response({"message": "Profile image deleted successfully"})
        return Response({"error": "No image to delete"}, status=status.HTTP_400_BAD_REQUEST)




#------------------- Social -------------------------



class SocialLinksView(generics.RetrieveUpdateAPIView):
    serializer_class = SocialLinksSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user

        
        if hasattr(user, "userprofile"): 
            obj, created = SocialLinks.objects.get_or_create(user=user)
            return obj

        
        elif hasattr(user, "academy"): 
            obj, created = SocialLinks.objects.get_or_create(academy=user.academy)
            return obj

        return None
