from django.core.management.base import BaseCommand
import os
import joblib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from app.models import User, UserSkill

class Command(BaseCommand):
    help = "Train ML model from user skills and save as model.pkl"

    def handle(self, *args, **options):
        all_skills = [
            "React.js", "Vue.js", "Angular", "Node.js", "Python", "Django",
            "SQL", "iOS", "Android", "React Native", "JavaScript",
            "UI/UX", "Product Designer", "Graphic Designer", "3D Modeler", "Content Creator"
        ]

        data = []
        for user in User.objects.all():
            user_skills_qs = UserSkill.objects.filter(user=user)
            skill_vector = {s: user_skills_qs.filter(skill__name=s).first().points if user_skills_qs.filter(skill__name=s).exists() else 0 for s in all_skills}

            try:
                target_job = user.profile.job.title
            except Exception:
                target_job = "Data Analyst"

            skill_vector['role'] = target_job
            data.append(skill_vector)

        if not data:
            self.stdout.write(self.style.WARNING("⚠️ No user data found. Training skipped."))
            return

        df = pd.DataFrame(data)
        X = df.drop("role", axis=1)
        y = df["role"]

        clf = DecisionTreeClassifier()
        clf.fit(X, y)

        model_path = os.path.join("app", "ml", "model.pkl")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(clf, model_path)

        self.stdout.write(self.style.SUCCESS("✅ ML Model trained and saved dynamically!"))
