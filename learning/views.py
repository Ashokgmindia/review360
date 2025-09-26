from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Subject, Topic
from .serializers import SubjectSerializer, TopicSerializer
from iam.mixins import CollegeScopedQuerysetMixin, IsAuthenticatedAndScoped, ActionRolePermission
from iam.permissions import RoleBasedPermission, FieldLevelPermission, TenantScopedPermission


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class SubjectViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.select_related("department", "college").order_by("name")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        # Only teachers can see subjects assigned to them
        if getattr(user, "role", None) == "teacher":
            try:
                from academics.models import Teacher
                teacher = Teacher.objects.get(user_id=user.id)
                # Filter subjects to only show those handled by this teacher
                qs = qs.filter(id__in=teacher.subjects_handled.filter(is_active=True).values_list('id', flat=True))
            except Teacher.DoesNotExist:
                # Teacher not found, return empty queryset
                return qs.none()
        return qs


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class TopicViewSet(CollegeScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("subject", "subject__college").order_by("subject", "name")
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticatedAndScoped, RoleBasedPermission, TenantScopedPermission, FieldLevelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["subject", "is_active"]
    search_fields = ["name", "context", "objectives"]
    ordering_fields = ["name", "created_at"]
    tenant_relations = ["subject__college_id"]  # Add tenant relation for college scoping
    
    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        
        # Only teachers can see topics from subjects assigned to them
        if getattr(user, "role", None) == "teacher":
            try:
                from academics.models import Teacher
                teacher = Teacher.objects.get(user_id=user.id)
                # Filter topics to only show those from subjects handled by this teacher
                teacher_subjects = teacher.subjects_handled.filter(is_active=True).values_list('id', flat=True)
                qs = qs.filter(subject_id__in=teacher_subjects)
            except Teacher.DoesNotExist:
                # Teacher not found, return empty queryset
                return qs.none()
        
        # Filter by subject if subject_id is provided in query params
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        
        return qs
    
    def perform_create(self, serializer):
        # The serializer will handle subject_id validation and subject assignment
        # No need for additional logic here as it's handled in the serializer
        serializer.save()


