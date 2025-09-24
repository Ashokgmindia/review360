from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import serializers
from django.db import transaction

from .models import Class, Student, Department, Teacher, StudentSubject
from .serializers import (
    ClassSerializer,
    StudentSerializer,
    DepartmentSerializer,
    TeacherSerializer,
    StudentSubjectsUpdateSerializer,
)
from .bulk_upload_utils import process_student_bulk_upload, BulkUploadError
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(
        tags=["Academics"],
        summary="Create a new class",
        description="Create a new class with optional student file upload. Students can be imported via Excel, CSV, or JSON file.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Class name'},
                    'academic_year': {'type': 'string', 'description': 'Academic year'},
                    'teacher': {'type': 'integer', 'description': 'Teacher ID'},
                    'section': {'type': 'string', 'description': 'Class section'},
                    'program': {'type': 'string', 'description': 'Program name'},
                    'semester': {'type': 'integer', 'description': 'Semester number'},
                    'room_number': {'type': 'string', 'description': 'Room number'},
                    'max_students': {'type': 'integer', 'description': 'Maximum number of students (optional)'},
                    'student_file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Excel (.xlsx), CSV (.csv), or JSON (.json) file containing student data'
                    }
                },
                'required': ['name', 'academic_year']
            }
        }
    ),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class ClassViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Class.objects.select_related("college", "teacher").order_by("name")
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active"]
    search_fields = ["name", "academic_year"]
    ordering_fields = ["name", "academic_year", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        # Additional narrowing for teachers inside their college
        if getattr(user, "role", None) == "teacher":
            # Class.teacher points to academics.Teacher, which links to iam.User via Teacher.user
            qs = qs.filter(teacher__user_id=user.id)
        return qs

    def perform_update(self, serializer):
        """Override to handle teacher assignment to existing class."""
        instance = serializer.save()
        
        # If teacher is being assigned to a class with existing students
        if instance.teacher and instance.students.exists():
            # Get all students in this class
            students = instance.students.filter(is_active=True)
            
            # Auto-assign teacher's subjects to existing students
            from .serializers import ClassSerializer
            class_serializer = ClassSerializer()
            class_serializer._assign_teacher_subjects_to_students(instance, students)
        
        return instance



@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class StudentViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Student.objects.select_related("class_ref", "department", "college").order_by("last_name", "first_name")
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active", "class_ref"]
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "academic_year"]

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        if getattr(user, "role", None) == "teacher":
            # Student.class_ref.teacher points to academics.Teacher; filter via related user
            qs = qs.filter(class_ref__teacher__user_id=user.id)
        return qs

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy method to properly delete the associated User account
        when deleting a Student (if user exists).
        """
        instance = self.get_object()
        user = instance.user
        
        # Store user ID before deletion for potential cleanup
        user_id = user.id if user else None
        
        # Delete the student instance (this should cascade delete the user due to CASCADE)
        self.perform_destroy(instance)
        
        # Double-check: if user still exists, delete it explicitly
        # This handles cases where CASCADE might not work as expected
        if user_id:
            from iam.models import User
            try:
                remaining_user = User.objects.get(id=user_id)
                remaining_user.delete()
            except User.DoesNotExist:
                # User was already deleted by CASCADE, which is good
                pass
        
        return Response({
            "message": "Student deleted successfully",
            "status": "success"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)')
    @extend_schema(
        tags=["Academics"],
        summary="Get students by class ID",
        description="Retrieve all students belonging to a specific class with their subjects and teacher information",
        responses={
            200: {
                'description': 'Paginated list of students in the class',
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'description': 'Total number of students'},
                    'next': {'type': 'string', 'nullable': True, 'description': 'URL for next page'},
                    'previous': {'type': 'string', 'nullable': True, 'description': 'URL for previous page'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'first_name': {'type': 'string'},
                                'last_name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'class_ref': {'type': 'integer'},
                                'subjects': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'name': {'type': 'string'},
                                            'code': {'type': 'string'},
                                            'teacher': {
                                                'type': 'object',
                                                'properties': {
                                                    'id': {'type': 'integer'},
                                                    'first_name': {'type': 'string'},
                                                    'last_name': {'type': 'string'},
                                                    'email': {'type': 'string'},
                                                    'employee_id': {'type': 'string'},
                                                    'designation': {'type': 'string'}
                                                }
                                            }
                                        }
                                    }
                                },
                                'topics': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'name': {'type': 'string'},
                                            'status': {'type': 'string'},
                                            'grade': {'type': 'integer'},
                                            'subject': {
                                                'type': 'object',
                                                'properties': {
                                                    'id': {'type': 'integer'},
                                                    'name': {'type': 'string'},
                                                    'code': {'type': 'string'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'class_info': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'academic_year': {'type': 'string'},
                            'teacher': {
                                'type': 'object',
                                'nullable': True,
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'first_name': {'type': 'string'},
                                    'last_name': {'type': 'string'},
                                    'email': {'type': 'string'},
                                    'employee_id': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    def get_students_by_class(self, request, class_id=None):
        """Get all students in a specific class with their subjects and teacher information."""
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get students in the class
        students = Student.objects.filter(
            class_ref=class_obj,
            is_active=True
        ).select_related('class_ref', 'department', 'college')
        
        # Apply any additional filtering based on user permissions
        user = getattr(request, "user", None)
        if getattr(user, "role", None) == "teacher":
            # Teachers can only see students from their classes
            students = students.filter(class_ref__teacher__user_id=user.id)
        
        # Use DRF's pagination
        page = self.paginate_queryset(students)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            
            # Add class_info to the paginated response
            paginated_response.data['class_info'] = {
                "id": class_obj.id,
                "name": class_obj.name,
                "academic_year": class_obj.academic_year,
                "teacher": {
                    "id": class_obj.teacher.id,
                    "first_name": class_obj.teacher.first_name,
                    "last_name": class_obj.teacher.last_name,
                    "email": class_obj.teacher.email,
                    "employee_id": class_obj.teacher.employee_id
                } if class_obj.teacher else None
            }
            
            return paginated_response
        
        # Fallback if pagination is not configured
        serializer = self.get_serializer(students, many=True)
        
        return Response({
            "count": students.count(),
            "next": None,
            "previous": None,
            "results": serializer.data,
            "class_info": {
                "id": class_obj.id,
                "name": class_obj.name,
                "academic_year": class_obj.academic_year,
                "teacher": {
                    "id": class_obj.teacher.id,
                    "first_name": class_obj.teacher.first_name,
                    "last_name": class_obj.teacher.last_name,
                    "email": class_obj.teacher.email,
                    "employee_id": class_obj.teacher.employee_id
                } if class_obj.teacher else None
            }
        })

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)/student/(?P<student_id>[^/.]+)')
    @extend_schema(
        tags=["Academics"],
        summary="Get specific student by class ID and student ID",
        description="Retrieve a specific student from a particular class with their subjects and teacher information",
        responses={
            200: {
                'description': 'Student details with subjects and teacher info',
                'type': 'object',
                'properties': {
                    'student': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'subjects': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'name': {'type': 'string'},
                                        'code': {'type': 'string'},
                                        'teacher': {
                                            'type': 'object',
                                            'properties': {
                                                'id': {'type': 'integer'},
                                                'first_name': {'type': 'string'},
                                                'last_name': {'type': 'string'},
                                                'email': {'type': 'string'},
                                                'employee_id': {'type': 'string'},
                                                'designation': {'type': 'string'}
                                            }
                                        }
                                    }
                                }
                            },
                            'topics': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'name': {'type': 'string'},
                                        'status': {'type': 'string'},
                                        'grade': {'type': 'integer'},
                                        'subject': {
                                            'type': 'object',
                                            'properties': {
                                                'id': {'type': 'integer'},
                                                'name': {'type': 'string'},
                                                'code': {'type': 'string'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'class_info': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'academic_year': {'type': 'string'},
                            'teacher': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'first_name': {'type': 'string'},
                                    'last_name': {'type': 'string'},
                                    'email': {'type': 'string'},
                                    'employee_id': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            },
            404: {'description': 'Student or class not found'}
        }
    )
    def get_student_by_class_and_id(self, request, class_id=None, student_id=None):
        """Get a specific student from a particular class with their subjects and teacher information."""
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            student = Student.objects.get(
                id=student_id,
                class_ref=class_obj,
                is_active=True
            )
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found in this class"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Apply permission checks
        user = getattr(request, "user", None)
        if getattr(user, "role", None) == "teacher":
            # Teachers can only see students from their classes
            if class_obj.teacher.user_id != user.id:
                return Response(
                    {"error": "Access denied"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Serialize the student
        serializer = self.get_serializer(student)
        
        return Response({
            "student": serializer.data,
            "class_info": {
                "id": class_obj.id,
                "name": class_obj.name,
                "academic_year": class_obj.academic_year,
                "teacher": {
                    "id": class_obj.teacher.id,
                    "first_name": class_obj.teacher.first_name,
                    "last_name": class_obj.teacher.last_name,
                    "email": class_obj.teacher.email,
                    "employee_id": class_obj.teacher.employee_id
                } if class_obj.teacher else None
            }
        })

    @action(detail=False, methods=['put', 'patch'], url_path='class/(?P<class_id>[^/.]+)/student/(?P<student_id>[^/.]+)/subjects', name='update-student-subjects')
    @extend_schema(
        tags=["Academics"],
        summary="Update student subject data for a particular class",
        description="Update subject assignments for a specific student in a particular class",
        request={
            'application/json': {
                'type': 'object',
                'required': ['subjects'],
                'properties': {
                    'subjects': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'required': ['subject_id'],
                            'properties': {
                                'subject_id': {'type': 'integer', 'description': 'ID of the subject', 'example': 1},
                                'teacher_id': {'type': 'integer', 'description': 'ID of the teacher (optional)', 'example': 2},
                                'is_active': {'type': 'boolean', 'description': 'Whether the assignment is active', 'default': True, 'example': True},
                                'topics': {
                                    'type': 'array',
                                    'description': 'List of topics to update for this subject',
                                    'items': {
                                        'type': 'object',
                                        'required': ['id'],
                                        'properties': {
                                            'id': {'type': 'integer', 'description': 'ID of the topic', 'example': 1},
                                            'status': {'type': 'string', 'enum': ['not_started', 'in_progress', 'validated'], 'description': 'Topic status', 'example': 'in_progress'},
                                            'grade': {'type': 'integer', 'minimum': 0, 'maximum': 10, 'description': 'Grade for the topic', 'example': 5},
                                            'comments_and_recommendations': {'type': 'string', 'description': 'Comments about the topic', 'example': 'Good progress'},
                                            'qns1_text': {'type': 'string', 'description': 'Question 1 text (admin only)', 'example': 'Question 1 text'},
                                            'qns1_checked': {'type': 'boolean', 'description': 'Whether question 1 is checked', 'example': True},
                                            'qns2_text': {'type': 'string', 'description': 'Question 2 text (admin only)', 'example': 'Question 2 text'},
                                            'qns2_checked': {'type': 'boolean', 'description': 'Whether question 2 is checked', 'example': True},
                                            'qns3_text': {'type': 'string', 'description': 'Question 3 text (admin only)', 'example': 'Question 3 text'},
                                            'qns3_checked': {'type': 'boolean', 'description': 'Whether question 3 is checked', 'example': False},
                                            'qns4_text': {'type': 'string', 'description': 'Question 4 text (admin only)', 'example': 'Question 4 text'},
                                            'qns4_checked': {'type': 'boolean', 'description': 'Whether question 4 is checked', 'example': False}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'example': {
                    'subjects': [
                        {
                            'subject_id': 1,
                            'teacher_id': 2,
                            'is_active': True,
                            'topics': [
                                {
                                    'id': 1,
                                    'status': 'in_progress',
                                    'grade': 5,
                                    'comments_and_recommendations': 'Good progress',
                                    'qns1_text': 'Question 1 text (admin only)',
                                    'qns1_checked': True,
                                    'qns2_text': 'Question 2 text (admin only)',
                                    'qns2_checked': True,
                                    'qns3_text': 'Question 3 text (admin only)',
                                    'qns3_checked': False,
                                    'qns4_text': 'Question 4 text (admin only)',
                                    'qns4_checked': False
                                }
                            ]
                        }
                    ]
                }
            }
        },
        operation_id="update_student_subjects_for_class",
        responses={
            200: {
                'description': 'Updated student subject assignments and topics',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'message': {'type': 'string', 'example': 'Student subject assignments and topics updated successfully'},
                                'updated_assignments': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer', 'example': 1},
                                            'subject_id': {'type': 'integer', 'example': 1},
                                            'teacher_id': {'type': 'integer', 'example': 2},
                                            'is_active': {'type': 'boolean', 'example': True},
                                            'created': {'type': 'boolean', 'example': False}
                                        }
                                    }
                                },
                                'updated_topics': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer', 'example': 1},
                                            'status': {'type': 'string', 'example': 'in_progress'},
                                            'grade': {'type': 'integer', 'example': 5},
                                            'comments_and_recommendations': {'type': 'string', 'example': 'Good progress'},
                                            'qns1_checked': {'type': 'boolean', 'example': True},
                                            'qns2_checked': {'type': 'boolean', 'example': True},
                                            'qns3_checked': {'type': 'boolean', 'example': False},
                                            'qns4_checked': {'type': 'boolean', 'example': False}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            404: {'description': 'Student or class not found'},
            400: {'description': 'Invalid data provided'}
        }
    )
    def get_serializer_class(self):
        """Override serializer class for the subjects update action."""
        if self.action == 'update_student_subjects_for_class':
            return StudentSubjectsUpdateSerializer
        return super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        """Override serializer for the subjects update action."""
        if self.action == 'update_student_subjects_for_class':
            return StudentSubjectsUpdateSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        """Override serializer context for the subjects update action."""
        context = super().get_serializer_context()
        if self.action == 'update_student_subjects_for_class':
            context['action'] = 'update_student_subjects_for_class'
        return context

    def update_student_subjects_for_class(self, request, class_id=None, student_id=None):
        """Update subject assignments for a specific student in a particular class."""
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            student = Student.objects.get(
                id=student_id,
                class_ref=class_obj,
                is_active=True
            )
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found in this class"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Apply permission checks
        user = getattr(request, "user", None)
        if getattr(user, "role", None) == "teacher":
            # Teachers can only update students from their classes
            if class_obj.teacher.user_id != user.id:
                return Response(
                    {"error": "Access denied"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Validate request data using serializer
        serializer = StudentSubjectsUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid data provided", "details": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subjects_data = serializer.validated_data.get('subjects', [])
        
        updated_assignments = []
        updated_topics = []
        
        try:
            with transaction.atomic():
                # Update or create subject assignments
                for subject_data in subjects_data:
                    subject_id = subject_data.get('subject_id')
                    teacher_id = subject_data.get('teacher_id')
                    is_active = subject_data.get('is_active', True)
                    topics_data = subject_data.get('topics', [])
                    
                    if not subject_id:
                        continue
                    
                    # Get the subject and teacher
                    try:
                        from learning.models import Subject
                        subject = Subject.objects.get(id=subject_id, is_active=True)
                    except Subject.DoesNotExist:
                        continue
                    
                    teacher = None
                    if teacher_id:
                        try:
                            teacher = Teacher.objects.get(id=teacher_id, is_active=True)
                        except Teacher.DoesNotExist:
                            continue
                    
                    # Update or create the assignment
                    assignment, created = StudentSubject.objects.update_or_create(
                        student=student,
                        subject=subject,
                        class_ref=class_obj,
                        defaults={
                            'teacher': teacher,
                            'is_active': is_active
                        }
                    )
                    
                    updated_assignments.append({
                        'id': assignment.id,
                        'subject_id': assignment.subject.id,
                        'teacher_id': assignment.teacher.id if assignment.teacher else None,
                        'is_active': assignment.is_active,
                        'created': created
                    })
                    
                    # Update topics for this subject
                    for topic_data in topics_data:
                        topic_id = topic_data.get('id')
                        if not topic_id:
                            continue
                        
                        try:
                            from learning.models import Topic
                            topic = Topic.objects.get(id=topic_id, subject=subject, is_active=True)
                            
                            # Apply role-based validation and updates
                            updated_topic = self._update_topic_with_validation(topic, topic_data, user)
                            if updated_topic:
                                updated_topics.append({
                                    'id': updated_topic.id,
                                    'status': updated_topic.status,
                                    'grade': updated_topic.grade,
                                    'comments_and_recommendations': updated_topic.comments_and_recommendations,
                                    'qns1_checked': updated_topic.qns1_checked,
                                    'qns2_checked': updated_topic.qns2_checked,
                                    'qns3_checked': updated_topic.qns3_checked,
                                    'qns4_checked': updated_topic.qns4_checked
                                })
                                
                        except Topic.DoesNotExist:
                            continue
                
                return Response({
                    "message": "Student subject assignments and topics updated successfully",
                    "updated_assignments": updated_assignments,
                    "updated_topics": updated_topics
                })
                
        except Exception as e:
            return Response(
                {"error": f"Failed to update assignments: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _update_topic_with_validation(self, topic, topic_data, user):
        """Update topic with role-based validation."""
        is_admin = getattr(user, 'role', None) == 'admin'
        is_teacher = getattr(user, 'role', None) == 'teacher'
        
        if is_admin:
            # Admin can update all fields
            update_fields = [
                'status', 'grade', 'comments_and_recommendations',
                'qns1_text', 'qns1_checked', 'qns2_text', 'qns2_checked',
                'qns3_text', 'qns3_checked', 'qns4_text', 'qns4_checked'
            ]
        elif is_teacher:
            # Teachers can only update validation fields
            update_fields = [
                'status', 'grade', 'comments_and_recommendations',
                'qns1_checked', 'qns2_checked', 'qns3_checked', 'qns4_checked'
            ]
            
            # Validate that at least 2 questions are checked (same as learning API)
            checked_count = sum([
                topic_data.get('qns1_checked', topic.qns1_checked),
                topic_data.get('qns2_checked', topic.qns2_checked),
                topic_data.get('qns3_checked', topic.qns3_checked),
                topic_data.get('qns4_checked', topic.qns4_checked)
            ])
            
            if checked_count < 2:
                raise serializers.ValidationError("At least 2 checkbox questions must be selected.")
        else:
            # Other roles cannot update topics
            return None
        
        # Update only allowed fields
        updated = False
        for field in update_fields:
            if field in topic_data:
                setattr(topic, field, topic_data[field])
                updated = True
        
        if updated:
            # Update status based on grade (same logic as Topic model)
            grade = topic_data.get('grade', topic.grade)
            if grade >= 7:
                topic.status = 'validated'
            elif grade > 0:
                topic.status = 'in_progress'
            else:
                topic.status = 'not_started'
            
            topic.save()
            return topic
        
        return None


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class DepartmentViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Department.objects.select_related("college", "hod").order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class TeacherViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related("user", "college", "department").prefetch_related("subjects_handled").order_by("last_name", "first_name")
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["department", "is_hod", "is_active"]
    search_fields = ["first_name", "last_name", "email", "employee_id"]
    ordering_fields = ["last_name", "first_name", "date_of_joining"]

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy method to properly delete the associated User account
        when deleting a Teacher.
        """
        instance = self.get_object()
        user = instance.user
        
        # Store user ID before deletion for potential cleanup
        user_id = user.id if user else None
        
        # Delete the teacher instance (this should cascade delete the user due to CASCADE)
        self.perform_destroy(instance)
        
        # Double-check: if user still exists, delete it explicitly
        # This handles cases where CASCADE might not work as expected
        if user_id:
            from iam.models import User
            try:
                remaining_user = User.objects.get(id=user_id)
                remaining_user.delete()
            except User.DoesNotExist:
                # User was already deleted by CASCADE, which is good
                pass
        
        return Response({
            "message": "Teacher deleted successfully",
            "status": "success"
        }, status=status.HTTP_200_OK)