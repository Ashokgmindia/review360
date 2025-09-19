from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Class, Student, Department, Subject, Teacher, Topic
from .serializers import (
    ClassSerializer,
    StudentSerializer,
    DepartmentSerializer,
    SubjectSerializer,
    TeacherSerializer,
    TopicSerializer,
)
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
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
            qs = qs.filter(teacher_id=user.id)
        return qs


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
            qs = qs.filter(class_ref__teacher_id=user.id)
        return qs



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
class SubjectViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.select_related("department", "college").order_by("name")
    serializer_class = SubjectSerializer
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


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class TopicViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("subject", "subject__college").order_by("subject", "order", "name")
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["subject", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "order", "created_at"]
    tenant_relations = ["subject__college_id"]  # Add tenant relation for college scoping
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by subject if subject_id is provided in query params
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        
        return qs
    
    def perform_create(self, serializer):
        # The serializer will handle subject_id validation and subject assignment
        # No need for additional logic here as it's handled in the serializer
        serializer.save()



