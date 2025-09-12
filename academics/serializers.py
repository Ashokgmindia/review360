from rest_framework import serializers
from .models import Class, Student, ImportLog


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
        ]
        read_only_fields = ["id"]


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


