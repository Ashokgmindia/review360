from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Class, Student, ImportLog
from .serializers import ClassSerializer, StudentSerializer, ImportLogSerializer


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all().order_by("name")
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active"]
    search_fields = ["name", "academic_year"]
    ordering_fields = ["name", "academic_year", "is_active"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
    create=extend_schema(tags=["Academics"]),
    update=extend_schema(tags=["Academics"]),
    partial_update=extend_schema(tags=["Academics"]),
    destroy=extend_schema(tags=["Academics"]),
)
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by("last_name", "first_name")
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["academic_year", "is_active", "class_ref"]
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "academic_year"]


@extend_schema_view(
    list=extend_schema(tags=["Academics"]),
    retrieve=extend_schema(tags=["Academics"]),
)
class ImportLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImportLog.objects.all().order_by("-imported_at")
    serializer_class = ImportLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["class_ref"]
    ordering_fields = ["imported_at", "imported_count", "errors_count"]


