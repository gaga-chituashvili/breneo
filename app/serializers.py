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
from .models import Academy,UserProfile,TemporaryUser
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
        model = TemporaryUser 
        fields = ["first_name", "last_name", "email", "password", "phone_number"]
        extra_kwargs = {"password": {"write_only": True}}
        validators = []

    def create(self, validated_data):
        # პაროლი hash-ით
        validated_data["password"] = make_password(validated_data["password"])

        # დროებითი ობიექტის შექმნა
        temp_user = TemporaryUser.objects.create(**validated_data)

        # 6-ნიშნა კოდის გენერაცია
        temp_user.generate_verification_code()

        return temp_user


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
            profile = getattr(user, "profile", None)
            phone_number = getattr(profile, "phone_number", None)
            profile_image_url = profile.profile_image.url if profile and profile.profile_image else None

            data.update({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": phone_number,
                "profile_image": profile_image_url,
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
                "profile_image": getattr(academy, "profile_image", None)  
            }

        raise AuthenticationFailed("Invalid email/full name or password.")