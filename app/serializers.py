from rest_framework import serializers
from .models import (
    Assessment,
    Badge,
    DynamicTechQuestion,
    CareerCategory,
    CareerQuestion,
    CareerOption,
    DynamicSoftSkillsQuestion,
    SkillTestResult,TemporaryAcademy,SocialLinks
)
from django.contrib.auth import authenticate,get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Academy,UserProfile,TemporaryUser
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()

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
    class Meta:
        model = TemporaryUser
        fields = ["first_name", "last_name", "email", "password", "phone_number"]
        extra_kwargs = {"password": {"write_only": True}}
        validators = []

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        temp_user = TemporaryUser.objects.create(**validated_data)
        temp_user.generate_verification_code()
        return temp_user

# --------------------------
# Academy Registration
# --------------------------
class TemporaryAcademyRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporaryAcademy
        fields = ["name", "email", "password", "phone_number", "description", "website"]
        extra_kwargs = {"password": {"write_only": True}}
        validators = []

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        temp_academy = TemporaryAcademy.objects.create(**validated_data)
        temp_academy.generate_verification_code()
        return temp_academy







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


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)





class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data









class UserProfileUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source="profile.phone_number", allow_blank=True, required=False)
    profile_image = serializers.ImageField(source="profile.profile_image", allow_null=True, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "profile_image"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": False},
        }

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists():
            raise serializers.ValidationError("this mail already taken")
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})

        # update user fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)

        if "phone_number" in profile_data:
            profile.phone_number = profile_data.get("phone_number")

        if "profile_image" in profile_data:
            profile.profile_image = profile_data.get("profile_image")

        profile.save()
        return instance


class AcademyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Academy
        fields = ["name", "email", "phone_number", "description", "website"]
        extra_kwargs = {
            "name": {"required": False},
            "email": {"required": False},
            "phone_number": {"required": False},
            "description": {"required": False},
            "website": {"required": False},
        }

    def validate_email(self, value):
        request = self.context.get("request")
        academy = getattr(request, "academy", None) 
        instance = getattr(self, "instance", None)
        qs = Academy.objects.exclude(pk=instance.pk) if instance else Academy.objects.all()
        if qs.filter(email__iexact=value).exists():
            raise serializers.ValidationError("this mail already taken")
        return value




#------------ User Change Password -------------------


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    


#------------ Academy Change Password -----------------



class AcademyChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def validate_old_password(self, value):
        academy = self.context['request'].user
        if not check_password(value, academy.password):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    




#------------------- person information -----------------

class UserProfileSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ["id", "phone_number", "profile_image", "profile_image_url"]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def update(self, instance, validated_data):
        instance.phone_number = validated_data.get("phone_number", instance.phone_number)
        if "profile_image" in validated_data:
            instance.profile_image = validated_data["profile_image"]
        instance.save()
        return instance







class SocialLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLinks
        fields = "__all__"
        read_only_fields = ["user", "academy"]










