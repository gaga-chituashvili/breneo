from django.contrib.auth.models import User

User.objects.all()
# ან კონკრეტული იუზერის მოძებნა
User.objects.filter(username="gaga1919")
print(User.objects.filter(username="gaga1919"))