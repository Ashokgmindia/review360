from rest_framework import serializers
from django.db import transaction
from iam.models import User
from iam.permissions import FieldLevelPermission
from typing import List, Dict, Any, Optional
from .models import Class, Student, Department, Teacher, StudentSubject, StudentTopicProgress, StudentClassEnrollment


class ClassSerializer(serializers.ModelSerializer):
    # Add file upload field for student import
    student_file = serializers.FileField(
        write_only=True, 
        required=False, 
        help_text="Excel, CSV, or JSON file containing student data",
        allow_empty_file=False,
        use_url=False
    )
    # Add class overall grade field
    class_overall_grade = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            "id",
            "name",
            "academic_year",
            "is_active",
            "college",
            "teacher",
            "section",
            "program",
            "semester",
            "room_number",
            "max_students",
            "student_file",  # File upload field
            "class_overall_grade",  # Class overall grade field
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "college", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        
        # Extract student file before creating class
        student_file = validated_data.pop('student_file', None)
        
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
        
        # Set the college field - always use the user's college
        validated_data['college'] = college
        
        # Create the class
        class_instance = Class.objects.create(**validated_data)
        print(f"DEBUG: Created class with ID: {class_instance.id}, Name: {class_instance.name}")
        
        # Handle student file upload if provided
        if student_file:
            try:
                from .bulk_upload_utils import process_student_bulk_upload, BulkUploadError
                
                # Process student bulk upload with target class
                print(f"DEBUG: Processing student upload for class ID: {class_instance.id}")
                result = process_student_bulk_upload(student_file, college, user, target_class=class_instance)
                
                # Store upload results in class metadata for reference
                class_instance.metadata = {
                    'student_upload_result': {
                        'success_count': result['success_count'],
                        'new_students_created': result.get('new_students_created', 0),
                        'existing_students_added': result.get('existing_students_added', 0),
                        'error_count': result['error_count'],
                        'errors': result['errors']
                    }
                }
                class_instance.save()
                
                # Auto-assign teacher's subjects to students if teacher is assigned
                if class_instance.teacher and result['success_count'] > 0:
                    # Get all students enrolled in this class (both new and existing)
                    enrollments = StudentClassEnrollment.objects.filter(
                        class_ref=class_instance,
                        is_active=True
                    ).select_related('student')
                    students_in_class = [enrollment.student for enrollment in enrollments]
                    self._assign_teacher_subjects_to_students(class_instance, students_in_class)
                
            except BulkUploadError as e:
                # If student upload fails, still create the class but add error to metadata
                class_instance.metadata = {
                    'student_upload_error': str(e)
                }
                class_instance.save()
            except Exception as e:
                # If any other error occurs, still create the class
                class_instance.metadata = {
                    'student_upload_error': f"Unexpected error: {str(e)}"
                }
                class_instance.save()
        
        return class_instance

    def _assign_teacher_subjects_to_students(self, class_instance, students):
        """Helper method to assign teacher's subjects to students and create topic progress."""
        teacher = class_instance.teacher
        if not teacher:
            return
        
        # Get teacher's subjects that are active
        teacher_subjects = teacher.subjects_handled.filter(is_active=True)
        
        # Create StudentSubject assignments for each student and subject
        student_subject_assignments = []
        student_topic_progress_assignments = []
        
        for student in students:
            for subject in teacher_subjects:
                # Check if assignment already exists
                if not StudentSubject.objects.filter(
                    student=student,
                    subject=subject,
                    class_ref=class_instance
                ).exists():
                    student_subject_assignments.append(
                        StudentSubject(
                            student=student,
                            subject=subject,
                            teacher=teacher,
                            class_ref=class_instance
                        )
                    )
                    
                    # Create topic progress for all topics in this subject
                    from learning.models import Topic
                    topics = Topic.objects.filter(subject=subject, is_active=True)
                    for topic in topics:
                        # Check if topic progress already exists
                        if not StudentTopicProgress.objects.filter(
                            student=student,
                            topic=topic,
                            class_ref=class_instance
                        ).exists():
                            student_topic_progress_assignments.append(
                                StudentTopicProgress(
                                    student=student,
                                    topic=topic,
                                    subject=subject,
                                    class_ref=class_instance,
                                    status='not_started',
                                    grade=0,
                                    comments_and_recommendations='',
                                    qns1_text=topic.qns1_text,
                                    qns2_text=topic.qns2_text,
                                    qns3_text=topic.qns3_text,
                                    qns4_text=topic.qns4_text,
                                )
                            )
        
        # Bulk create assignments
        if student_subject_assignments:
            StudentSubject.objects.bulk_create(student_subject_assignments)
        
        if student_topic_progress_assignments:
            StudentTopicProgress.objects.bulk_create(student_topic_progress_assignments)

    def get_class_overall_grade(self, obj: Class) -> float:
        """Calculate overall class grade from all students' grades in this class."""
        # Get all students enrolled in this class
        enrollments = StudentClassEnrollment.objects.filter(
            class_ref=obj,
            is_active=True
        ).select_related('student')
        
        if not enrollments.exists():
            return 0.0
        
        # Calculate overall grade for each student and then average them
        student_grades = []
        for enrollment in enrollments:
            student = enrollment.student
            
            # Get all topic progress records for this student in this class
            student_topic_progress = StudentTopicProgress.objects.filter(
                student=student,
                class_ref=obj,
                is_active=True
            )
            
            if student_topic_progress.exists():
                # Calculate average grade from all topic grades for this student (including 0 grades)
                grades = [progress.grade for progress in student_topic_progress]
                if grades:
                    student_average = sum(grades) / len(grades)
                    student_grades.append(student_average)
                else:
                    # If no grades exist, treat as 0
                    student_grades.append(0.0)
            else:
                # If no topic progress exists, treat as 0
                student_grades.append(0.0)
        
        # Calculate class overall grade
        if student_grades:
            return round(sum(student_grades) / len(student_grades), 2)
        else:
            return 0.0


class StudentSerializer(serializers.ModelSerializer):
    # Custom fields to display subjects and topics based on class
    subjects = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    student_grade = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birth_date",
            "blood_group",
            "address",
            "profile_photo",
            "class_ref",
            "academic_year",
            "college",
            "department",
            "student_number",
            "admission_date",
            "graduation_date",
            "status",
            "guardian_name",
            "guardian_contact",
            "is_active",
            "metadata",
            "subjects",
            "topics",
            "student_grade",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_subjects(self, obj: Student) -> List[Dict[str, Any]]:
        """Get all subjects assigned to the student with teacher information."""
        if not obj.class_ref:
            return []
        
        # Get student's assigned subjects with teacher info
        student_subjects = StudentSubject.objects.filter(
            student=obj,
            class_ref=obj.class_ref,
            is_active=True
        ).select_related('subject', 'teacher', 'subject__department')
        
        return [
            {
                "id": assignment.subject.id,
                "name": assignment.subject.name,
                "code": assignment.subject.code,
                "description": assignment.subject.description,
                "semester": assignment.subject.semester,
                "credits": assignment.subject.credits,
                "is_elective": assignment.subject.is_elective,
                "department": {
                    "id": assignment.subject.department.id,
                    "name": assignment.subject.department.name,
                    "code": assignment.subject.department.code
                } if assignment.subject.department else None,
                "teacher": {
                    "id": assignment.teacher.id,
                    "first_name": assignment.teacher.first_name,
                    "last_name": assignment.teacher.last_name,
                    "email": assignment.teacher.email,
                    "employee_id": assignment.teacher.employee_id,
                    "designation": assignment.teacher.designation
                } if assignment.teacher else None,
                "assigned_at": assignment.assigned_at
            }
            for assignment in student_subjects
        ]

    def get_topics(self, obj: Student) -> List[Dict[str, Any]]:
        """Get all topics from subjects assigned to the student with student-specific progress."""
        if not obj.class_ref:
            return []
        
        # Get student's topic progress records
        from .models import StudentTopicProgress
        student_topic_progress = StudentTopicProgress.objects.filter(
            student=obj,
            class_ref=obj.class_ref,
            is_active=True
        ).select_related('topic', 'topic__subject').order_by('topic__id')
        
        
        return [
            {
                "id": progress.topic.id,
                "name": progress.topic.name,
                "context": progress.topic.context,
                "objectives": progress.topic.objectives,
                "status": progress.status,  # Use student-specific status
                "grade": progress.grade,  # Use student-specific grade
                "comments_and_recommendations": progress.comments_and_recommendations,  # Use student-specific comments
                "subject": {
                    "id": progress.topic.subject.id,
                    "name": progress.topic.subject.name,
                    "code": progress.topic.subject.code
                },
                "questions": [
                    {"text": progress.qns1_text, "checked": progress.qns1_checked},
                    {"text": progress.qns2_text, "checked": progress.qns2_checked},
                    {"text": progress.qns3_text, "checked": progress.qns3_checked},
                    {"text": progress.qns4_text, "checked": progress.qns4_checked}
                ]
            }
            for progress in student_topic_progress
        ]

    def get_student_grade(self, obj: Student) -> float:
        """Calculate overall student grade from all topic grades."""
        if not obj.class_ref:
            return 0.0
        
        # Get all topic progress records for this student
        from .models import StudentTopicProgress
        student_topic_progress = StudentTopicProgress.objects.filter(
            student=obj,
            class_ref=obj.class_ref,
            is_active=True
        )
        
        if not student_topic_progress.exists():
            return 0.0
        
        # Calculate average grade from all topic grades
        grades = [progress.grade for progress in student_topic_progress if progress.grade > 0]
        if grades:
            return round(sum(grades) / len(grades), 2)
        else:
            return 0.0

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
            
        # Field-level permission validation
        user_role = getattr(user, "role", None)
        if user_role == "student":
            # Students cannot modify academic details
            readonly_fields = ["class_ref", "academic_year", "college", "department", "student_number", "status"]
            for field in readonly_fields:
                if field in attrs:
                    raise serializers.ValidationError({field: f"Students cannot modify {field}"})
        elif user_role == "teacher":
            # Teachers have limited access to student data
            readonly_fields = ["class_ref", "academic_year", "college", "department", "student_number", "status"]
            for field in readonly_fields:
                if field in attrs:
                    raise serializers.ValidationError({field: f"Teachers cannot modify {field}"})
        
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


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code", "hod", "college", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

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
        return Department.objects.create(**validated_data)




class TeacherSerializer(serializers.ModelSerializer):
    # Create linked user
    password = serializers.CharField(write_only=True, min_length=8)
    # Custom field to display subject names
    subjects_handled_names = serializers.SerializerMethodField()

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
            "subjects_handled_names",
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

    def get_subjects_handled_names(self, obj: Teacher) -> List[Dict[str, Any]]:
        """Return list of subject names and codes for the teacher."""
        subjects = obj.subjects_handled.filter(is_active=True)
        return [
            {
                "id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "semester": subject.semester,
                "credits": subject.credits
            }
            for subject in subjects
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        # Extract subjects_handled before creating teacher
        subjects_handled = validated_data.pop("subjects_handled", [])
        
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
            # Create teacher without subjects_handled
            teacher = Teacher.objects.create(user=linked_user, college=college, **validated_data)
            
            # Set subjects_handled after teacher is created
            if subjects_handled:
                teacher.subjects_handled.set(subjects_handled)
            
            return teacher

    def update(self, instance, validated_data):
        # Extract subjects_handled before updating teacher
        subjects_handled = validated_data.pop("subjects_handled", None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update subjects_handled if provided
        if subjects_handled is not None:
            instance.subjects_handled.set(subjects_handled)
        
        return instance


class StudentSubjectUpdateSerializer(serializers.Serializer):
    """Serializer for updating student subject assignments with topics."""
    subject_id = serializers.IntegerField(help_text="ID of the subject")
    teacher_id = serializers.IntegerField(required=False, allow_null=True, help_text="ID of the teacher (optional)")
    is_active = serializers.BooleanField(default=True, help_text="Whether the assignment is active")
    topics = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="List of topics to update for this subject"
    )

    def validate_subject_id(self, value):
        """Validate that the subject exists and is active."""
        from learning.models import Subject
        try:
            subject = Subject.objects.get(id=value, is_active=True)
            return value
        except Subject.DoesNotExist:
            raise serializers.ValidationError("Subject with this ID does not exist or is not active.")

    def validate_teacher_id(self, value):
        """Validate that the teacher exists and is active."""
        if value is None:
            return value
        try:
            teacher = Teacher.objects.get(id=value, is_active=True)
            return value
        except Teacher.DoesNotExist:
            raise serializers.ValidationError("Teacher with this ID does not exist or is not active.")

    def validate_topics(self, value):
        """Validate topics data structure."""
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        user_role = getattr(user, 'role', None) if user else None
        
        for topic_data in value:
            if not isinstance(topic_data, dict):
                raise serializers.ValidationError("Each topic must be a dictionary.")
            
            # Validate required fields for topics
            if 'id' not in topic_data:
                raise serializers.ValidationError("Each topic must have an 'id' field.")
            
            # Validate topic ID exists
            topic_id = topic_data.get('id')
            if topic_id:
                from learning.models import Topic
                try:
                    Topic.objects.get(id=topic_id, is_active=True)
                except Topic.DoesNotExist:
                    raise serializers.ValidationError(f"Topic with ID {topic_id} does not exist or is not active.")
            
            # Role-based validation for topic fields
            if user_role == 'teacher':
                # Teachers can now update all fields including question text
                # Validate that at least 2 questions are checked for teachers
                checked_count = sum([
                    topic_data.get('qns1_checked', False),
                    topic_data.get('qns2_checked', False),
                    topic_data.get('qns3_checked', False),
                    topic_data.get('qns4_checked', False)
                ])
                
                if checked_count < 2:
                    raise serializers.ValidationError("At least 2 checkbox questions must be selected.")
            
            elif user_role not in ['admin', 'college_admin']:
                # Only teachers, admins, and college_admins can update topics
                raise serializers.ValidationError("Insufficient permissions to update topic data.")
        
        return value


class StudentSubjectsUpdateSerializer(serializers.Serializer):
    """Serializer for the main request body."""
    subjects = serializers.ListField(
        child=StudentSubjectUpdateSerializer(),
        required=True,
        help_text="List of subjects to update for the student"
    )

    def validate_subjects(self, value):
        """Validate that at least one subject is provided."""
        if not value:
            raise serializers.ValidationError("At least one subject must be provided.")
        return value

    class Meta:
        # This helps with OpenAPI schema generation
        ref_name = "StudentSubjectsUpdate"


class StudentSubjectsResponseSerializer(serializers.Serializer):
    """Serializer for the response of student subjects update API."""
    subjects = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of updated subject assignments"
    )

    class Meta:
        ref_name = "StudentSubjectsResponse"
