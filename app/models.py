from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



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

class Question(models.Model):
    text = models.TextField()
    domain = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=10)
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.IntegerField()

    def __str__(self):
        return f"{self.domain} - {self.text[:50]}"


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