# from django.core.mail import send_mail
# from django.conf import settings
# from django.urls import reverse
# from itsdangerous import URLSafeTimedSerializer

# def generate_verification_token(email):
#     serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
#     return serializer.dumps(email, salt="email-verification")

# def confirm_verification_token(token, max_age=3600):
#     serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
#     try:
#         email = serializer.loads(token, salt="email-verification", max_age=max_age)
#     except Exception:
#         return None
#     return email

# def send_verification_email(obj, academy=False):
#     """
#     obj: User ან Academy ობიექტი
#     academy: თუ True, მაშინ Academy ვაფიქსირებთ
#     """
#     token = generate_verification_token(obj.email)

#     if academy:
#         verify_url = f"https://breneo.onrender.com/api/verify-academy-email/?token={token}"
#         name = getattr(obj, 'name', obj.email)  
#     else:
#         verify_url = f"https://breneo.onrender.com/api/verify-email/?token={token}"
#         name = getattr(obj, 'first_name', obj.email) 

#     subject = "Verify your email"
#     message = f"Hi {name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [obj.email])





# app/utils.py
import threading
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt="email-verification")

def confirm_verification_token(token, max_age=86400):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(token, salt="email-verification", max_age=max_age)
    except Exception:
        return None
    return email

def _send_mail_thread(subject, message, recipient_list):
    try:
        # fail_silently=True prevents exceptions from breaking the worker;
        # use False locally when debugging to see errors
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=True
        )
        print(f"[mail] sent to {recipient_list}")
    except Exception as e:
        # log error — in production use proper logging (logger.exception)
        print(f"[mail] send failed: {e}")

def send_verification_email(obj, academy=False):
    token = generate_verification_token(obj.email)

    if academy:
        verify_url = f"https://breneo.onrender.com/api/verify-academy-email/?token={token}"
        name = getattr(obj, 'name', obj.email)
    else:
        verify_url = f"https://breneo.onrender.com/api/verify-email/?token={token}"
        name = getattr(obj, 'first_name', obj.email)

    subject = "Verify your email"
    message = f"Hi {name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"

    # run in background thread: avoids blocking the request
    thread = threading.Thread(target=_send_mail_thread, args=(subject, message, [obj.email]), daemon=True)
    thread.start()
