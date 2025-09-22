from django.contrib import admin
from iam.models import User

from .models import Subject, Topic


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "college", "semester", "is_active", "created_at")
    search_fields = ("name", "code", "description")
    list_filter = ("department", "college", "semester", "is_active", "is_elective")
    ordering = ("name",)

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


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "status", "grade", "qns1_checked", "qns2_checked", "qns3_checked", "qns4_checked", "is_active", "created_at")
    list_filter = ("is_active", "status", "subject", "qns1_checked", "qns2_checked", "qns3_checked", "qns4_checked", "created_at")
    search_fields = ("name", "context", "objectives", "subject__name", "qns1_text", "qns2_text", "qns3_text", "qns4_text")
    list_editable = ("is_active",)
    ordering = ("subject", "name")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "subject")
        }),
        ("Content", {
            "fields": ("context", "objectives")
        }),
        ("Progress & Evaluation", {
            "fields": ("status", "grade", "comments_and_recommendations")
        }),
        ("Question 1", {
            "fields": ("qns1_text", "qns1_checked"),
            "classes": ("collapse",)
        }),
        ("Question 2", {
            "fields": ("qns2_text", "qns2_checked"),
            "classes": ("collapse",)
        }),
        ("Question 3", {
            "fields": ("qns3_text", "qns3_checked"),
            "classes": ("collapse",)
        }),
        ("Question 4", {
            "fields": ("qns4_text", "qns4_checked"),
            "classes": ("collapse",)
        }),
        ("Organization", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ("created_at", "updated_at")
    
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
                return qs.filter(subject__college_id__in=college_ids)
        return qs.none()
    
    def clean(self):
        """Admin-level validation (no request context available here)."""
        # Validation is handled at serializer level where request context is available
        pass