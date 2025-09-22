from rest_framework import serializers
from typing import List, Dict, Any
from .models import ActivitySheet, Validation, Subject, Topic


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


class SubjectSerializer(serializers.ModelSerializer):
    topics = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = [
            "id", "name", "code", "description", "department", 
            "college", "semester", "credits", "is_elective", 
            "is_active", "syllabus_file", "topics", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_topics(self, obj) -> List[Dict[str, Any]]:
        """Get topics for this subject."""
        topics = obj.topics.filter(is_active=True)
        return TopicSerializer(topics, many=True, context=self.context).data

    def create(self, validated_data):
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
        
        # Set the college field
        validated_data['college'] = college
        return Subject.objects.create(**validated_data)


class TopicSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(write_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Topic
        fields = [
            "id", "name", "context", "objectives", "status", "grade", 
            "comments_and_recommendations", 
            "qns1_text", "qns1_checked", "qns2_text", "qns2_checked", 
            "qns3_text", "qns3_checked", "qns4_text", "qns4_checked",
            "subject_id", "subject_name", "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate(self, attrs):
        """Validate that at least 2 questions are selected for PUT requests only."""
        # Get the request method from context
        request = self.context.get('request')
        if request and request.method == 'PUT':
            selected_questions = sum([
                attrs.get('qns1_checked', False),
                attrs.get('qns2_checked', False),
                attrs.get('qns3_checked', False),
                attrs.get('qns4_checked', False)
            ])
            
            if selected_questions < 2:
                raise serializers.ValidationError("At least 2 questions must be selected.")
        
        return attrs
    
    def create(self, validated_data):
        # Extract subject_id and remove it from validated_data
        subject_id = validated_data.pop('subject_id')
        
        # Get the subject object
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            raise serializers.ValidationError("Subject with this ID does not exist.")
        
        # Create the topic with the subject
        return Topic.objects.create(subject=subject, **validated_data)


