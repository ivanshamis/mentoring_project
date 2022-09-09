from django.contrib.auth import authenticate
from rest_framework import serializers

from user.backends import validate_token, validate_password
from user.constants import ErrorMessages, MIN_PASSWORD_LENGTH
from user.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, write_only=True
    )

    def validate(self, data):
        if not validate_password(data["password"]):
            raise serializers.ValidationError(ErrorMessages.WEAK_PASSWORD_SPEC)
        return data

    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def create(self, validated_data):
        return self.Meta.model.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, write_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def create(self, validated_data):
        user = authenticate(
            username=validated_data["username"], password=validated_data["password"]
        )
        if not user:
            raise serializers.ValidationError(ErrorMessages.USER_WRONG_CREDENTIALS)
        if not user.is_active:
            raise serializers.ValidationError(ErrorMessages.USER_IS_DEACTIVATED)

        return user

    def update(self, instance, validated_data):
        pass


class PasswordSetupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, read_only=True)
    token = serializers.CharField(max_length=500, write_only=True)
    password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, write_only=True
    )

    def validate(self, data):
        user, _ = validate_token(
            token=data["token"], action="password", invalidate=True
        )
        if not user:
            raise serializers.ValidationError(ErrorMessages.INVALID_TOKEN)
        data["user"] = user
        if not validate_password(data["password"]):
            raise serializers.ValidationError(ErrorMessages.WEAK_PASSWORD_SPEC)
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        pass


class PasswordChangeSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, read_only=True)
    old_password = serializers.CharField(max_length=128, min_length=1, write_only=True)
    password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, write_only=True
    )
    password_repeat = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, write_only=True
    )

    def validate(self, data):
        if data["old_password"] == data["password"]:
            raise serializers.ValidationError(ErrorMessages.PASSWORD_THE_SAME)
        if data["password"] != data["password_repeat"]:
            raise serializers.ValidationError(ErrorMessages.PASSWORD_NO_MATCH)
        if not validate_password(data["password"]):
            raise serializers.ValidationError(ErrorMessages.WEAK_PASSWORD_SPEC)
        return data

    def update(self, instance, validated_data):
        user = instance
        if not user.check_password(validated_data["old_password"]):
            raise serializers.ValidationError(ErrorMessages.PASSWORD_IS_WRONG)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def create(self, validated_data):
        pass


class ActivationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    def validate(self, data):
        token = self.context["request"].query_params.get("token")
        user, _ = validate_token(token=token, action="activate", invalidate=True)
        if not user:
            raise serializers.ValidationError(ErrorMessages.INVALID_TOKEN)
        data["user"] = user
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        pass


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
        )
        read_only_fields_for_all = ("id", "email")
        read_only_fields = read_only_fields_for_all + ("is_active", "is_staff")


class AdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = UserSerializer.Meta.read_only_fields_for_all


class AdminCreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "is_staff"]

    def create(self, validated_data):
        return self.Meta.model.objects.create_user(**validated_data)
