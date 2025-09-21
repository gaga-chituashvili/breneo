from rest_framework import serializers
from .models import Assessment, Badge,DynamicTechQuestion,CareerCategory, CareerQuestion, CareerOption,DynamicSoftSkillsQuestion,TestResult

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['name', 'status', 'completed_at']

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['name', 'achieved_at']




class QuestionTechSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicTechQuestion
        fields = [
            "id",
            "questionid",
            "questiontext",
            "RoleMapping",
            "skill",
            'difficulty',
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_option",
            "isactive",
            "createdat",
            "updatedat",
        ]



class CareerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerOption
        fields = ['id', 'text', 'RoleMapping']

class CareerQuestionSerializer(serializers.ModelSerializer):
    options = CareerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = CareerQuestion
        fields = ['id', 'text', 'options']

class CareerCategorySerializer(serializers.ModelSerializer):
    questions = CareerQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = CareerCategory
        fields = ['id', 'code', 'title', 'questions']




class QuestionSoftSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicSoftSkillsQuestion
        fields = [
            "id",
            "questionid",
            "questiontext",
            "RoleMapping",
            "skill",
            'difficulty',
            "option1",
            "option2",
            "option3",
            "option4",
            "correct_option",
            "isactive",
            "createdat",
            "updatedat",
        ]






class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['id', 'user', 'tech_question', 'soft_question', 'answer', 'score', 'created_at']
        read_only_fields = ['id', 'created_at', 'score', 'user']  
