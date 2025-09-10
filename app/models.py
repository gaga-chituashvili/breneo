from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid



class Assessment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.status})"

class Badge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    achieved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"




class AssessmentSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    current_question_index = models.IntegerField(default=0)
    questions = models.JSONField(default=list)  
    answers = models.JSONField(default=list)   
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Session {self.id} - Completed: {self.completed}"
    


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    points = models.IntegerField(default=1)

class Job(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=False, default="No description")
    salary_min = models.IntegerField(null=False, default=0)
    salary_max = models.IntegerField(null=False, default=0)
    time_to_ready = models.CharField(max_length=50, default="Not specified")
    required_skills = models.ManyToManyField(Skill, related_name="jobs")

class Course(models.Model):
    title = models.CharField(max_length=200)
    skills_taught = models.ManyToManyField(Skill, related_name="courses")




class DynamicTechQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    questionid = models.CharField(max_length=50, unique=True)
    skill = models.CharField(max_length=100,default='')
    RoleMapping = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10,default='easy')
    questiontext = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.IntegerField(default=1)
    isactive = models.BooleanField(default=True)
    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.skill} - {self.questiontext[:50]}"



class CareerCategory(models.Model):
    code = models.CharField(max_length=5, unique=True) 
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.title}"


class CareerQuestion(models.Model):
    category = models.ForeignKey(CareerCategory, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return f"{self.category.code}{self.id}: {self.text[:50]}"


class CareerOption(models.Model):
    question = models.ForeignKey(CareerQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    RoleMapping = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.text} → {self.RoleMapping}"
    


class DynamicSoftSkillsQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    questionid = models.CharField(max_length=50, unique=True)
    skill = models.CharField(max_length=100,default='')
    RoleMapping = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10,default='easy')
    questiontext = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.IntegerField(default=1)
    isactive = models.BooleanField(default=True)
    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.skill} - {self.questiontext[:50]}"
    



class SkillScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0) 
    threshold = models.FloatField(default=70.0) 
    created_at = models.DateTimeField(auto_now_add=True)

    def is_strong(self):
        return self.score >= self.threshold

    def __str__(self):
        status = "✅ Strong" if self.is_strong() else "❌ Weak"
        return f"{self.user.username} - {self.skill.name}: {self.score}% ({status})"