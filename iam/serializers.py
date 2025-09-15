from rest_framework import serializers
from django.db import transaction
from .models import User, College


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    colleges = serializers.PrimaryKeyRelatedField(queryset=College.objects.all(), many=True, required=False)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "role", "college", "colleges")

    def create(self, validated_data):
        password = validated_data.pop("password")
        colleges = validated_data.pop("colleges", [])
        email = validated_data.get("email")
        username = email
        user = User.objects.create_user(username=username, **validated_data)
        user.set_password(password)
        user.save()
        if colleges:
            user.colleges.set(colleges)
        # Ensure legacy FK is present if a single college submitted in colleges
        if not user.college_id and colleges:
            try:
                user.college = colleges[0]
                user.save(update_fields=["college"])
            except Exception:
                pass
        return user


class CollegeSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(write_only=True)
    admin_username = serializers.CharField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)
    admin_role = serializers.ChoiceField(write_only=True, choices=[(User.Role.COLLEGE_ADMIN, "College Admin")], default=User.Role.COLLEGE_ADMIN)

    class Meta:
        model = College
        fields = [
            "id",
            "name",
            "code",
            "address",
            "city",
            "state",
            "postcode",
            "country",
            "contact_email",
            "contact_phone",
            "is_active",
            "admin",
            "admin_email",
            "admin_username",
            "admin_password",
            "admin_role",
        ]
        read_only_fields = ["id", "admin"]

    def create(self, validated_data):
        admin_email = validated_data.pop("admin_email")
        admin_username = validated_data.pop("admin_username")
        admin_password = validated_data.pop("admin_password")
        admin_role = validated_data.pop("admin_role", User.Role.COLLEGE_ADMIN)
        # Always enforce role to college_admin
        if admin_role != User.Role.COLLEGE_ADMIN:
            raise serializers.ValidationError({"admin_role": "Only College Admin is allowed."})
        with transaction.atomic():
            college = College.objects.create(**validated_data)
            # Create admin user
            # Ensure uniqueness with clear errors
            if User.objects.filter(username=admin_username).exists():
                raise serializers.ValidationError({"admin_username": "Username already exists."})
            if User.objects.filter(email=admin_email).exists():
                raise serializers.ValidationError({"admin_email": "Email already exists."})
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
            try:
                admin_user.colleges.add(college)
            except Exception:
                pass
            return college


class EmailTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.CharField(read_only=True)
    college = serializers.IntegerField(allow_null=True, read_only=True)
    colleges = serializers.ListField(child=serializers.IntegerField(), read_only=True)


