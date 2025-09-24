from rest_framework import serializers
from typing import Dict, Any, Optional
from .models import FollowUpSession


class FollowUpSessionSerializer(serializers.ModelSerializer):
    # Add computed fields for better API response
    student_info = serializers.SerializerMethodField()
    topic_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    
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
            "notes_for_student",
            "status",
            "google_calendar_event_id",
            "academic_year",
            "student_info",
            "topic_info",
            "teacher_info",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "student_name", "subject_name", "topic_name", "teacher_name"]
    
    def get_student_info(self, obj: FollowUpSession) -> Optional[Dict[str, Any]]:
        """Get student information."""
        if obj.student:
            return {
                "id": obj.student.id,
                "name": f"{obj.student.first_name} {obj.student.last_name}",
                "email": obj.student.email,
                "student_number": obj.student.student_number,
                "class_name": obj.student.class_ref.name if obj.student.class_ref else None,
            }
        return None
    
    def get_topic_info(self, obj: FollowUpSession) -> Optional[Dict[str, Any]]:
        """Get topic information."""
        if obj.topic:
            return {
                "id": obj.topic.id,
                "name": obj.topic.name,
                "context": obj.topic.context,
                "objectives": obj.topic.objectives,
                "subject_name": obj.topic.subject.name if obj.topic.subject else None,
            }
        return None
    
    def get_teacher_info(self, obj: FollowUpSession) -> Optional[Dict[str, Any]]:
        """Get teacher information."""
        if obj.teacher:
            return {
                "id": obj.teacher.id,
                "name": f"{obj.teacher.first_name} {obj.teacher.last_name}",
                "email": obj.teacher.email,
                "employee_id": obj.teacher.employee_id,
                "designation": obj.teacher.designation,
            }
        return None
    
    def create(self, validated_data):
        """Override create to automatically populate name fields."""
        # Auto-populate name fields from related objects
        student = validated_data.get('student')
        if student:
            validated_data['student_name'] = f"{student.first_name} {student.last_name}"
        
        subject = validated_data.get('subject')
        if subject:
            validated_data['subject_name'] = subject.name
        
        topic = validated_data.get('topic')
        if topic:
            validated_data['topic_name'] = topic.name
        
        teacher = validated_data.get('teacher')
        if teacher:
            validated_data['teacher_name'] = f"{teacher.first_name} {teacher.last_name}"
        
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Override update to automatically populate name fields."""
        # Auto-populate name fields from related objects
        student = validated_data.get('student', instance.student)
        if student:
            validated_data['student_name'] = f"{student.first_name} {student.last_name}"
        
        subject = validated_data.get('subject', instance.subject)
        if subject:
            validated_data['subject_name'] = subject.name
        
        topic = validated_data.get('topic', instance.topic)
        if topic:
            validated_data['topic_name'] = topic.name
        
        teacher = validated_data.get('teacher', instance.teacher)
        if teacher:
            validated_data['teacher_name'] = f"{teacher.first_name} {teacher.last_name}"
        
        return super().update(instance, validated_data)

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


