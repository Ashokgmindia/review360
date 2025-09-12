from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import ActivitySheet, Validation
from .serializers import ActivitySheetSerializer, ValidationSerializer


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class ActivitySheetViewSet(viewsets.ModelViewSet):
    queryset = ActivitySheet.objects.all().order_by("-created_at")
    serializer_class = ActivitySheetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["sheet_type", "status", "academic_year"]
    search_fields = ["student_name", "title", "context", "objectives", "methodology"]
    ordering_fields = ["created_at", "updated_at", "final_grade"]


@extend_schema_view(
    list=extend_schema(tags=["Learning"]),
    retrieve=extend_schema(tags=["Learning"]),
    create=extend_schema(tags=["Learning"]),
    update=extend_schema(tags=["Learning"]),
    partial_update=extend_schema(tags=["Learning"]),
    destroy=extend_schema(tags=["Learning"]),
)
class ValidationViewSet(viewsets.ModelViewSet):
    queryset = Validation.objects.all().order_by("-validation_date")
    serializer_class = ValidationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["activity_sheet"]
    ordering_fields = ["validation_date", "session_grade"]


