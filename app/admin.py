from django.contrib import admin
from .models import Question,Assessment,AssessmentSession, Badge,Job,Skill,UserSkill,Course

admin.site.register(Assessment)
admin.site.register(Badge)
admin.site.register(Job)
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(Course)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'domain', 'difficulty')
    search_fields = ('text', 'domain')

@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'completed')
    list_filter = ('completed', 'start_time')


