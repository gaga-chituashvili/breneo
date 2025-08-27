from rest_framework import serializers
from .models import Assessment, Badge, Question,DynamicTestQuestion

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['name', 'status', 'completed_at']

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['name', 'achieved_at']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['text','domain','difficulty', 'option1', 'option2', 'option3', 'option4', 'correct_option']



class QuestionTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicTestQuestion
        fields = [
            "id",
            "questionid",
            "questiontext",
            "category",
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_option",
            "isactive",
            "createdat",
            "updatedat",
        ]