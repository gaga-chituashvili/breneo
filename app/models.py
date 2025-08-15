from django.db import models
from django.contrib.auth.models import User

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
    option1 = models.CharField(max_length=255, default="Default Option")
    option2 = models.CharField(max_length=255, default="Default Option")
    option3 = models.CharField(max_length=255, default="Default Option")
    option4 = models.CharField(max_length=255, default="Default Option")
    correct_option = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.domain} - {self.text[:50]}"

class AssessmentSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    current_question = models.ForeignKey(
        Question, null=True, blank=True, on_delete=models.SET_NULL
    )
    completed = models.BooleanField(default=False)

    def __str__(self):
        status = 'Completed' if self.completed else 'In Progress'
        return f"{self.user.username} - {status}"
