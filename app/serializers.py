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
from .models import Academy,UserProfile
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import make_password, check_password

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






class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password", "phone_number"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        validated_data["password"] = make_password(validated_data["password"])
        user = User.objects.create_user(
            username=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        if phone_number:
            UserProfile.objects.create(user=user, phone_number=phone_number)
        return user


# --------------------------
# Academy Registration
# --------------------------
class AcademyRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Academy
        fields = ["name", "email", "password", "phone_number", "description", "website"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return Academy.objects.create(**validated_data)


# --------------------------
# Token Serializer
# --------------------------

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get("username") 
        password = attrs.get("password")

        user = None

        # ვცადოთ email-ით პოვნა
        user = User.objects.filter(email__iexact=identifier).first()

       
        if not user and " " in identifier:
            first_name, last_name = identifier.split(" ", 1)
            user = User.objects.filter(
                first_name__iexact=first_name.strip(),
                last_name__iexact=last_name.strip()
            ).first()

        
        if user and user.check_password(password):
            attrs["username"] = user.email
            data = super().validate(attrs)
            phone_number = getattr(user.profile, "phone_number", None)
            data.update({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": phone_number,
                "user_type": "user"
            })
            return data

       
        academy = Academy.objects.filter(email__iexact=identifier).first()
        if academy and check_password(password, academy.password):
            return {
                "access": "academy-access-token-placeholder",
                "refresh": "academy-refresh-placeholder",
                "user_type": "academy",
                "name": academy.name,
                "email": academy.email,
                "phone_number": academy.phone_number,
            }

        
        raise AuthenticationFailed("Invalid email/full name or password.")