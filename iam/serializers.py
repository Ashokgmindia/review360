from rest_framework import serializers
from .models import User, College


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "role", "college")

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.get("email")
        username = email
        user = User.objects.create_user(username=username, **validated_data)
        user.set_password(password)
        user.save()
        return user


class CollegeSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(write_only=True)
    admin_username = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = College
        fields = [
            "id",
            "name",
            "code",
            "address",
            "city",
            "state",
            "country",
            "contact_email",
            "contact_phone",
            "is_active",
            "admin",
            "admin_email",
            "admin_username",
            "admin_password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        admin_email = validated_data.pop("admin_email")
        admin_username = validated_data.pop("admin_username")
        admin_password = validated_data.pop("admin_password")
        college = College.objects.create(**validated_data)
        # Create admin user
        admin_user = User.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            role=User.Role.COLLEGE_ADMIN,
            college=college,
            is_staff=True,
        )
        college.admin = admin_user
        college.save()
        return college


class EmailTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


