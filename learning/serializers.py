from rest_framework import serializers
from .models import ActivitySheet, Validation


class ActivitySheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySheet
        fields = [
            "id",
            "college",
            "student",
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
        college = attrs.get("college")
        # Assign default college if not provided and exactly one allowed
        if college is None and len(allowed) == 1:
            attrs["college"] = attrs["college"] or getattr(user, "college")
        college = attrs.get("college")
        if college is None:
            raise serializers.ValidationError({"college": "College is required."})
        if college.id not in allowed:
            raise serializers.ValidationError({"college": "Not allowed for this user."})
        student = attrs.get("student")
        if student is not None and student.college_id != college.id:
            raise serializers.ValidationError({"student": "Student must belong to the same college."})
        return attrs


class ValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Validation
        fields = [
            "id",
            "college",
            "activity_sheet",
            "teacher",
            "has_subject",
            "context_well_formulated",
            "objectives_validated",
            "methodology_respected",
            "session_grade",
            "comments",
            "validation_date",
        ]
        read_only_fields = ["id", "validation_date"]

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
        college = attrs.get("college")
        # Default to user's single allowed college if not provided
        if college is None and len(allowed) == 1:
            attrs["college"] = attrs["college"] or getattr(user, "college")
        college = attrs.get("college")
        if college is None:
            raise serializers.ValidationError({"college": "College is required."})
        if college.id not in allowed:
            raise serializers.ValidationError({"college": "Not allowed for this user."})
        activity_sheet = attrs.get("activity_sheet")
        if activity_sheet and activity_sheet.college_id != college.id:
            raise serializers.ValidationError({"activity_sheet": "Must belong to same college."})
        teacher = attrs.get("teacher")
        if teacher and getattr(teacher, "college_id", None) not in (college.id, None):
            raise serializers.ValidationError({"teacher": "Must belong to same college."})
        return attrs


