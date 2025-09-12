from rest_framework import serializers
from .models import ActivitySheet, Validation


class ActivitySheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySheet
        fields = [
            "id",
            "student_name",
            "sheet_type",
            "sheet_number",
            "title",
            "context",
            "objectives",
            "methodology",
            "status",
            "final_grade",
            "academic_year",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Validation
        fields = [
            "id",
            "activity_sheet",
            "has_subject",
            "context_well_formulated",
            "objectives_validated",
            "methodology_respected",
            "session_grade",
            "comments",
            "validation_date",
        ]
        read_only_fields = ["id", "validation_date"]


