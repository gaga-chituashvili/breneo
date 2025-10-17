from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from itsdangerous import URLSafeTimedSerializer

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt="email-verification")

def confirm_verification_token(token, max_age=3600):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(token, salt="email-verification", max_age=max_age)
    except Exception:
        return None
    return email

def send_verification_email(user):
    token = generate_verification_token(user.email)
    verify_url = f"https://breneo.onrender.com//api/verify-email/?token={token}"

    subject = "Verify your email"
    message = f"Hi {user.first_name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
