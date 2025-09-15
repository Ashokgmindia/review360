from django.contrib import admin
from iam.models import User

from .models import AuditLog, ArchiveRecord


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("table_name", "action", "record_id", "college", "user", "created_at")
    search_fields = ("table_name", "action")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = []
            try:
                college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            if college_ids:
                return qs.filter(college_id__in=college_ids)
        return qs.none()


@admin.register(ArchiveRecord)
class ArchiveRecordAdmin(admin.ModelAdmin):
    list_display = ("table_name", "original_id", "college", "archived_at")
    search_fields = ("table_name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = []
            try:
                college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            if college_ids:
                return qs.filter(college_id__in=college_ids)
        return qs.none()


