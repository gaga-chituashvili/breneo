import json, random
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from app.models import DynamicSoftSkillsQuestion, AssessmentSession
from app.views import StartSoftAssessmentAPI, SubmitSoftAnswerAPI, FinishSoftAssessmentAPI

rf = RequestFactory()

print("\n=== START SOFT ASSESSMENT ===")
# Step 1: Start assessment
req = rf.post("/api/start-soft/", data={}, content_type="application/json")
resp = StartSoftAssessmentAPI.as_view()(req)
data = json.loads(resp.rendered_content)
print("StartSoftAssessmentAPI =>", data)

session_id = data["session_id"]
questions = [data["first_question"]]
session = AssessmentSession.objects.get(id=session_id)

# მოიძიოთ ყველა კითხვა სესიიდან (10-მდე)
questions = session.questions

print("\n=== SUBMIT ANSWERS ===")
for i, q in enumerate(questions):
    # შევარჩიოთ random option ან ყველა სწორი
    correct_opt = q[f"option{q['correct_option']}"]
    answer = correct_opt if random.random() > 0.3 else q["option1"]
    payload = {
        "session_id": session_id,
        "answer": answer,
        "question_text": q["questiontext"]
    }
    req = rf.post("/api/submit-soft/", data=json.dumps(payload), content_type="application/json")
    resp = SubmitSoftAnswerAPI.as_view()(req)
    print(f"Q{i+1} =>", json.loads(resp.rendered_content))

print("\n=== FINISH ASSESSMENT ===")
payload = {"session_id": session_id}
req = rf.post("/api/finish-soft/", data=json.dumps(payload), content_type="application/json")
resp = FinishSoftAssessmentAPI.as_view()(req)
print("FinishSoftAssessmentAPI =>", json.loads(resp.rendered_content))
