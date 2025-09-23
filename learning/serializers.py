from rest_framework import serializers
from typing import List, Dict, Any
from .models import Subject, Topic


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
        """Role-based validation for topic fields."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return attrs
            
        user = request.user
        is_teacher = user.role == 'teacher'
        
        # For teachers: validate that at least 2 questions are checked
        if is_teacher:
            selected_questions = sum([
                attrs.get('qns1_checked', False),
                attrs.get('qns2_checked', False),
                attrs.get('qns3_checked', False),
                attrs.get('qns4_checked', False)
            ])
            
            if selected_questions < 2:
                raise serializers.ValidationError("At least 2 checkbox questions must be selected.")
        
        return attrs
    
    def to_representation(self, instance):
        """Filter fields based on user role when serializing."""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            user = request.user
            is_teacher = user.role == 'teacher'
            
            # For teachers, remove fields they shouldn't see
            if is_teacher:
                restricted_fields = ['name', 'context', 'objectives']
                for field in restricted_fields:
                    if field in data:
                        del data[field]
        
        return data
    
    def to_internal_value(self, data):
        """Filter fields based on user role when deserializing."""
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            user = request.user
            is_teacher = user.role == 'teacher'
            
            # For teachers, remove fields they shouldn't be able to update
            if is_teacher:
                restricted_fields = ['name', 'context', 'objectives']
                for field in restricted_fields:
                    if field in data:
                        raise serializers.ValidationError({
                            field: f"Teachers do not have permission to update the '{field}' field."
                        })
        
        return super().to_internal_value(data)
    
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


