from rest_framework.test import APIRequestFactory
from app.views import RecommendedJobsAPI
from app.models import User, UserSkill, Job

# ====== Setup ======
user = User.objects.first()
if not user:
    raise Exception("No demo user in DB")

# Optional: add some skills for testing
UserSkill.objects.get_or_create(user=user, skill_id=1, defaults={"points": 5})
UserSkill.objects.get_or_create(user=user, skill_id=2, defaults={"points": 3})

# ====== API Request ======
factory = APIRequestFactory()
request = factory.get('/api/recommended-jobs/')

view = RecommendedJobsAPI.as_view()
response = view(request)

# ====== შედეგი ======
print(response.data)
