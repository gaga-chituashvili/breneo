import joblib
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Assessment, Badge, AssessmentSession, UserSkill, Job, Course, DynamicTechQuestion,Skill,CareerCategory,DynamicSoftSkillsQuestion,SkillScore
from .serializers import QuestionTechSerializer,CareerCategorySerializer,QuestionSoftSkillsSerializer
from django.contrib.auth.models import User
import os, requests, random
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics
from .models import CareerQuestion
from .serializers import CareerQuestionSerializer
import json






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
        completed_count = assessments.filter(status='completed').count()
        in_progress_count = assessments.filter(status='in_progress').count()
        current_session = AssessmentSession.objects.filter(user=user, completed=False).first()

       
        user_skills = UserSkill.objects.filter(user=user)
        skill_summary = {us.skill.name: us.level for us in user_skills}

       
        jobs_data = []
        for job in Job.objects.all():
            match = calculate_match(user_skills, job)
            jobs_data.append(match)

       
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
    permission_classes = []

    def get(self, request):
        questions = list(DynamicTechQuestion.objects.filter(isactive=True))
        random.shuffle(questions)
        serializer = QuestionTechSerializer(questions, many=True)
        return Response(serializer.data)
    

class DynamicSoftSkillsquestionsAPI(APIView):
    permission_classes = []

    def get(self, request):
        questions = list(DynamicSoftSkillsQuestion.objects.filter(isactive=True))
        random.shuffle(questions)
        serializer = QuestionSoftSkillsSerializer(questions, many=True)
        return Response(serializer.data)





class CareerCategoryListAPIView(generics.ListAPIView):
    queryset = CareerCategory.objects.all()
    serializer_class = CareerCategorySerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]

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
        user = User.objects.first() or User.objects.create(username="demo_user")
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
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                return Response({"error": "Missing session_id"}, status=status.HTTP_400_BAD_REQUEST)

            # მიიღეთ session
            try:
                session = AssessmentSession.objects.get(id=session_id)
            except AssessmentSession.DoesNotExist:
                return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

            # Load answers
            answers = session.answers or []
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except Exception:
                    answers = []

            skill_scores = {}
            skill_totals = {}

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

            # Calculate per skill and update UserSkill & SkillScore
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

            # Mark session completed
            session.completed = True
            session.save()

            # Determine final role based on strongest skill (case-insensitive)
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
                "kubernetes": "DevOps Engineer"
            }

            final_role = "N/A"
            if results:
                # Normalize keys to lowercase
                normalized_role_mapping = {k.lower(): v for k, v in role_mapping.items()}
                # Get strongest skill, lowercase
                strongest_skill = max(
                    results.items(),
                    key=lambda item: float(item[1]['percentage'].replace('%', ''))
                )[0].strip().lower()
                # Lookup final role safely
                final_role = normalized_role_mapping.get(strongest_skill, "N/A")

            return Response({
                "message": "Assessment finished successfully",
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


class RandomCareerQuestionsAPI(APIView):
    authentication_classes = []
    permission_classes = []

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




