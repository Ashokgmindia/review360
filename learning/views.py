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
        
        # Filter by subject if subject_id is provided in query params
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        
        return qs
    
    def perform_create(self, serializer):
        # The serializer will handle subject_id validation and subject assignment
        # No need for additional logic here as it's handled in the serializer
        serializer.save()


