from rest_framework import serializers
from .models import FollowUpSession


class FollowUpSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpSession
        fields = [
            "id",
            "college",
            "student",
            "subject",
            "topic",
            "teacher",
            "student_name",
            "subject_name",
            "topic_name",
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
        if college is None and len(allowed) == 1:
            attrs["college"] = attrs["college"] or getattr(user, "college")
        college = attrs.get("college")
        if college is None:
            raise serializers.ValidationError({"college": "College is required."})
        if college.id not in allowed:
            raise serializers.ValidationError({"college": "Not allowed for this user."})
        student = attrs.get("student")
        if student and student.college_id != college.id:
            raise serializers.ValidationError({"student": "Must belong to same college."})
        subject = attrs.get("subject")
        if subject and subject.college_id != college.id:
            raise serializers.ValidationError({"subject": "Must belong to same college."})
        topic = attrs.get("topic")
        if topic and topic.subject.college_id != college.id:
            raise serializers.ValidationError({"topic": "Must belong to same college."})
        teacher = attrs.get("teacher")
        if teacher and getattr(teacher, "college_id", None) not in (college.id, None):
            raise serializers.ValidationError({"teacher": "Must belong to same college."})
        return attrs


