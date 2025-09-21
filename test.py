import os, django, json, uuid
import pandas as pd
import joblib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breneo1.settings")
django.setup()

from django.contrib.auth.models import User
from app.models import (
    AssessmentSession,
    DynamicTechQuestion,
    DynamicSoftSkillsQuestion,
    TestResult,
    UserSkill,
    SkillScore,
    Skill,
    AssessmentResult
)

# 1️⃣ შექმნა ან აღდგენა რეალური მომხმარებლის
username = "real_user"
user, created = User.objects.get_or_create(username=username)
if created:
    user.set_password("password123")
    user.save()
    print(f"User created: {username}")
else:
    print(f"User exists: {username}")

# 2️⃣ ახალი session
session = AssessmentSession.objects.create(user=user, completed=False)
print(f"Session created: {session.id}")

# 3️⃣ Tech პასუხები (მაგალითი)
tech_answers = [
    {"text": "Which is used to create a React component", "answer": "this.setState()"},
    {"text": "Vue directive for conditional rendering", "answer": "v-if"},
    {"text": "Angular HTTP request handler", "answer": "Manage HTTP requests, share data"},
    {"text": "Graphic Design tool for vector graphics", "answer": "Made of pixels"},
    {"text": "React Native state management", "answer": "setState()"},
]

# 4️⃣ Soft პასუხები (მაგალითი)
soft_answers = [
    {"question_text": "Adaptability & Learning", "answer": "Excellent"},
    {"question_text": "Task Management", "answer": "Excellent"},
    {"question_text": "Time & Task Management", "answer": "Excellent"},
]

# 5️⃣ ჩაწერა TestResult tech
for ans in tech_answers:
    question = DynamicTechQuestion.objects.filter(questiontext__iexact=ans["text"]).first()
    TestResult.objects.create(
        user=user,
        tech_question=question,
        answer=ans["answer"],
        score=None
    )
    print(f"Saved tech result: {user.username} - {ans['text']} - {ans['answer']}")

# 6️⃣ ჩაწერა TestResult soft
for ans in soft_answers:
    question = DynamicSoftSkillsQuestion.objects.filter(questiontext__iexact=ans["question_text"]).first()
    TestResult.objects.create(
        user=user,
        soft_question=question,
        answer=ans["answer"],
        score=None
    )
    print(f"Saved soft result: {user.username} - {ans['question_text']} - {ans['answer']}")

# 7️⃣ Session mark as completed
session.completed = True
session.save()

# 8️⃣ გაანგარიშება per skill (Tech)
skill_scores = {}
skill_totals = {}

for tr in TestResult.objects.filter(user=user, tech_question__isnull=False):
    skill_name = tr.tech_question.skill if tr.tech_question else "Unknown"
    correct_option = getattr(tr.tech_question, "correct_option", None)
    correct_answer = getattr(tr.tech_question, f"option{correct_option}", "").strip() if correct_option else ""
    
    skill_scores.setdefault(skill_name, 0)
    skill_totals.setdefault(skill_name, 0)
    skill_totals[skill_name] += 1
    if tr.answer.strip() == correct_answer:
        skill_scores[skill_name] += 1

results = {}
threshold_strong = 70.0
threshold_borderline = 60.0

for skill_name, correct_count in skill_scores.items():
    total = skill_totals.get(skill_name, 0)
    percentage = round((correct_count / total) * 100, 2) if total else 0.0

    skill_obj, _ = Skill.objects.get_or_create(name=skill_name)
    user_skill, _ = UserSkill.objects.get_or_create(user=user, skill=skill_obj)
    user_skill.points += correct_count
    user_skill.save()

    SkillScore.objects.create(user=user, skill=skill_obj, score=percentage, threshold=threshold_strong)

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

# 9️⃣ Final role prediction (fallback)
final_role = "N/A"
if results:
    strongest_skill = max(results.items(), key=lambda item: float(item[1]["percentage"].replace("%", "")))[0].lower()
    role_mapping = {
        "react": "Frontend Developer",
        "vue": "Frontend Developer",
        "angular": "Frontend Developer",
        "javascript": "Frontend Developer",
        "python": "Backend Developer",
        "django": "Backend Developer",
        "node.js": "Backend Developer",
        "ios": "iOS Developer",
        "android": "Android Developer",
        "react native": "React Native Developer",
        "ui/ux": "UI/UX Designer",
        "graphic designer": "Graphic Designer",
        "3d modeler": "3D Modeler",
        "product designer": "Product Designer"
    }
    normalized_role_mapping = {k.lower(): v for k, v in role_mapping.items()}
    final_role = normalized_role_mapping.get(strongest_skill, "N/A")

# 10️⃣ AssessmentResult save
AssessmentResult.objects.create(
    user=user,
    session=session,
    total_score=total_score,
    total_questions=total_questions,
    final_role=final_role,
    tech_skills=results,
    soft_skills={}  # soft skills detailed calculation შესაძლებელია იგივე ლოგიკით
)

print(f"\nAssessment finished for session {session.id}!")
print(f"Total questions: {total_questions}")
print(f"Total score: {total_score}")
print("Results:")
for skill, data in results.items():
    print(f"{skill}: {data['score']} ({data['percentage']}) {data['recommendation']}")
print(f"Final Role: {final_role}")
