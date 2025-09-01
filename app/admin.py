from django.contrib import admin
from .models import Assessment,AssessmentSession, Badge,Job,Skill,UserSkill,Course,DynamicTechQuestion

admin.site.register(Assessment)
admin.site.register(Badge)
admin.site.register(Job)
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(Course)


@admin.register(DynamicTechQuestion)
class DynamicTechQuestion(admin.ModelAdmin):
    list_display = ('questiontext', 'skill','RoleMapping','difficulty')
    search_fields = ('questiontext', 'skill','RoleMapping')

