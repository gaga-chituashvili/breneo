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

def send_verification_email(obj, academy=False):
    """
    obj: User ან Academy ობიექტი
    academy: თუ True, მაშინ Academy ვაფიქსირებთ
    """
    token = generate_verification_token(obj.email)

    if academy:
        verify_url = f"https://breneo.onrender.com/api/verify-academy-email/?token={token}"
        name = getattr(obj, 'name', obj.email)  
    else:
        verify_url = f"https://breneo.onrender.com/api/verify-email/?token={token}"
        name = getattr(obj, 'first_name', obj.email) 

    subject = "Verify your email"
    message = f"Hi {name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [obj.email])


