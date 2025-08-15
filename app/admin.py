from django.contrib import admin
from .models import Question,Assessment,AssessmentSession, Badge

admin.site.register(Assessment)
admin.site.register(Badge)
admin.site.register(Question)
admin.site.register(AssessmentSession)