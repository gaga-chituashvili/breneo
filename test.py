from django.contrib.auth.models import User
from app.models import UserProfile
from app.utils import send_verification_email

# შექმნა ცარიელი user
user = User.objects.create_user(
    username="testuserრ3ff3rf43ფ@example.com",
    first_name="Test",
    last_name="User",
    email="gagachituashvili0@gmail.com",
    password="12345678"
)

# (თუ გინდა) profile
UserProfile.objects.create(user=user, phone_number="599123456")

# Email გაგზავნა
send_verification_email(user)