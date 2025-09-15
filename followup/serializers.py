from rest_framework import serializers
from .models import FollowUpSession


class FollowUpSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpSession
        fields = [
            "id",
            "college",
            "student",
            "activity_sheet",
            "teacher",
            "student_name",
            "activity_sheet_title",
            "teacher_name",
            "session_datetime",
            "location",
            "objective",
            "status",
            "google_calendar_event_id",
            "academic_year",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


