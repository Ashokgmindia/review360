from rest_framework import serializers
from django.db import transaction
from iam.models import User
from .models import Class, Student, ImportLog, Department, Subject, Teacher


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name", "academic_year", "is_active"]
        read_only_fields = ["id"]


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "class_ref",
            "academic_year",
            "is_active",
            "department",
            "student_number",
            "birth_date",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ImportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportLog
        fields = [
            "id",
            "class_ref",
            "filename",
            "imported_count",
            "errors_count",
            "error_details",
            "imported_at",
        ]
        read_only_fields = ["id", "imported_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code", "hod", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "code", "department"]
        read_only_fields = ["id"]


class TeacherSerializer(serializers.ModelSerializer):
    # Create linked user
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Teacher
        fields = [
            "id",
            # core
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "date_of_birth",
            "address",
            "profile_photo",
            "employee_id",
            "date_of_joining",
            "is_active",
            # role
            "designation",
            "department",
            "role_type",
            "is_hod",
            "reporting_to",
            # academic
            "highest_qualification",
            "specialization",
            "experience_years",
            "subjects_handled",
            "research_publications",
            "certifications",
            "resume",
            # auth
            "password",
            # meta
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        request = self.context.get("request")
        user = getattr(request, "user", None)
        college = getattr(user, "college", None)
        if college is None and getattr(user, "role", None) != User.Role.SUPERADMIN:
            raise serializers.ValidationError({"college": "College cannot be determined for current user."})
        with transaction.atomic():
            # Create linked user account
            username = validated_data["email"]
            if User.objects.filter(email=validated_data["email"]).exists():
                raise serializers.ValidationError({"email": "Email already exists."})
            linked_user = User.objects.create_user(
                username=username,
                email=validated_data["email"],
                password=password,
                role=User.Role.TEACHER,
                college=college,
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
            )
            teacher = Teacher.objects.create(user=linked_user, college=college, **validated_data)
            return teacher

