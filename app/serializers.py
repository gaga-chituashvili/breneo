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
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Academy
from rest_framework.exceptions import AuthenticationFailed

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



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        # ჯერ ვცადოთ Django User
        user = None
        try:
            user = User.objects.get(email=username_or_email)
            attrs["username"] = user.username
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                user = None

        if user:
            return super().validate(attrs)

        # თუ User არ მოიძებნა → ვცადოთ Academy
        try:
            academy = Academy.objects.get(email=username_or_email)
            if academy.password == password:
                # ტოკენისთვის pseudo-user ან custom response
                return {
                    "access": "academy-token-placeholder",
                    "refresh": "academy-refresh-placeholder",
                    "user_type": "academy",
                    "name": academy.name,
                    "email": academy.email,
                }
            else:
                raise AuthenticationFailed("Invalid credentials for academy")
        except Academy.DoesNotExist:
            raise AuthenticationFailed("No account found with given credentials.")




class AcademyRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Academy
        fields = ["name", "email", "password", "description", "website"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return Academy.objects.create(**validated_data)