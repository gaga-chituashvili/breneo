import os
import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from app.models import User, UserSkill, Job, Skill

# 1️⃣ ყველა შესაძლო სქილები (feature names)
all_skills = ["React.js", "Vue.js", "Angular", "Node.js", "Python", "Django",
              "SQL", "iOS", "Android", "React Native", "JavaScript",
              "UI/UX", "Product Designer", "Graphic Designer", "3D Modeler", "Content Creator"]

data = []

# 2️⃣ თითოეული User-ისთვის ვქმნით feature vector-ს
for user in User.objects.all():
    user_skills_qs = UserSkill.objects.filter(user=user)
    
    skill_vector = {}
    for skill_name in all_skills:
        us = user_skills_qs.filter(skill__name=skill_name).first()
        skill_vector[skill_name] = us.points if us else 0

    # 3️⃣ Target Job: შეიძლება აიღო UserProfile ან სხვა mapping
    # თუ User-ს ჯერ არ აქვს Job, გამოტოვეთ
    try:
        # თუ Job უკვე მიმაგრებულია (UserProfile.job), აიღეთ იქიდან
        target_job = user.profile.job.title  # შეცვალე თუ სხვანაირად გაქვს
    except Exception:
        # დეფოლტი, მაგალითად Data Analyst
        target_job = "Data Analyst"

    skill_vector['role'] = target_job
    data.append(skill_vector)

# 4️⃣ შექმნა DataFrame
df = pd.DataFrame(data)
X = df.drop("role", axis=1)
y = df["role"]

# 5️⃣ Decision Tree მოდელი
clf = DecisionTreeClassifier()
clf.fit(X, y)

# 6️⃣ შენახვა
model_path = os.path.join("app", "ml", "model.pkl")
os.makedirs(os.path.dirname(model_path), exist_ok=True)
joblib.dump(clf, model_path)
print("✅ ML Model trained and saved dynamically!")
