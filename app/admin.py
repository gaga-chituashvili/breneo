from django.contrib import admin
from .models import (
    Assessment, AssessmentSession, Badge,
    Job, Skill, UserSkill, Course,
    DynamicTechQuestion,
    CareerCategory, CareerQuestion, CareerOption,DynamicSoftSkillsQuestion,SkillScore,Academy,UserProfile,TemporaryUser,TemporaryAcademy,SkillTestResult,SocialLinks
)
admin.site.register(Assessment)
admin.site.register(Badge)
admin.site.register(Job)
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(Course)
admin.site.register(UserProfile)
admin.site.register(TemporaryUser)
admin.site.register(TemporaryAcademy)



@admin.register(DynamicTechQuestion)
class DynamicTechQuestionAdmin(admin.ModelAdmin):
    list_display = ('questiontext', 'skill', 'RoleMapping', 'difficulty')
    search_fields = ('questiontext', 'skill', 'RoleMapping')


@admin.register(CareerCategory)
class CareerCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'title')
    search_fields = ('code', 'title')


class CareerOptionInline(admin.TabularInline):
    model = CareerOption
    extra = 2


@admin.register(CareerQuestion)
class CareerQuestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'text')
    search_fields = ('text',)
    list_filter = ('category',)
    inlines = [CareerOptionInline]


@admin.register(CareerOption)
class CareerOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'RoleMapping')
    search_fields = ('text', 'RoleMapping')
    list_filter = ('RoleMapping',)



@admin.register(DynamicSoftSkillsQuestion)
class DynamicSoftSkillsQuestionAdmin(admin.ModelAdmin):
    list_display = ('questiontext', 'skill', 'RoleMapping', 'difficulty')
    search_fields = ('questiontext', 'skill', 'RoleMapping')



@admin.register(SkillScore)
class SkillScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "score", "threshold", "created_at")
    list_filter = ("user", "skill")



@admin.register(SkillTestResult)
class SkillTestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'final_role', 'total_score', 'created_at')
    search_fields = ('user__username', 'final_role')
    list_filter = ('final_role', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)



@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number','password','website', 'created_at')
    search_fields = ('name', 'email')



@admin.register(SocialLinks)
class SocialLinks(admin.ModelAdmin):
    list_display = ('user', 'academy')
    search_fields = ('user', 'academy')
