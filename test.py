from app.models import UserSkill
from django.db.models import Count

duplicates = UserSkill.objects.values('user', 'skill') \
    .annotate(count_id=Count('id')) \
    .filter(count_id__gt=1)

for dup in duplicates:
    objs = UserSkill.objects.filter(user_id=dup['user'], skill_id=dup['skill'])
    first = objs.first()  
    objs.exclude(id=first.id).delete()  