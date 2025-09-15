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

    def _allowed_college_ids(self, user):
        ids = []
        try:
            ids = list(getattr(user, "colleges").values_list("id", flat=True))
        except Exception:
            ids = []
        if getattr(user, "college_id", None):
            ids.append(user.college_id)
        return list({cid for cid in ids if cid})

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return attrs
        allowed = self._allowed_college_ids(user)
        # Infer or validate college from class_ref or department
        class_ref = attrs.get("class_ref")
        department = attrs.get("department")
        target_college_id = None
        if class_ref is not None:
            target_college_id = class_ref.college_id
        elif department is not None:
            target_college_id = department.college_id
        # Fallback to user's single college if determinable
        if target_college_id is None and len(allowed) == 1:
            target_college_id = allowed[0]
        if target_college_id is None:
            raise serializers.ValidationError({"college": "College cannot be determined. Provide class_ref/department from same college."})
        if target_college_id not in allowed:
            raise serializers.ValidationError({"college": "Not allowed for this user."})
        return attrs


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
        # Determine college from creator; superadmin must specify via user's single allowed or error
        allowed = []
        try:
            allowed = list(getattr(user, "colleges").values_list("id", flat=True))
        except Exception:
            allowed = []
        if getattr(user, "college_id", None):
            allowed.append(user.college_id)
        allowed = list({cid for cid in allowed if cid})
        college = getattr(user, "college", None)
        if college is None:
            if len(allowed) == 1:
                from iam.models import College
                college = College.objects.get(id=allowed[0])
            else:
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

