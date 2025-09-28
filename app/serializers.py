from rest_framework import serializers
from .models import (
    Assessment,
    Badge,
    DynamicTechQuestion,
    CareerCategory,
    CareerQuestion,
    CareerOption,
    DynamicSoftSkillsQuestion,
    SkillTestResult,
)

# --------------------------
# Assessment & Badge
# --------------------------
class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'name', 'status', 'completed_at']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'achieved_at']


# --------------------------
# Technical Questions
# --------------------------
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


# --------------------------
# Career Questions
# --------------------------
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


# --------------------------
# Soft Skills Questions
# --------------------------
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


class SkillTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillTestResult
        fields = ['id', 'user', 'final_role', 'total_score', 'skills_json', 'created_at']
        read_only_fields = ['user', 'created_at']
