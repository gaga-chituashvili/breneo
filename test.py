from app.models import UserProfile
p = UserProfile.objects.get(user__email="gagachituashvili7@gmail.com")
p.is_verified