from django.contrib import admin
from iam.models import User

from .models import FollowUpSession


@admin.register(FollowUpSession)
class FollowUpSessionAdmin(admin.ModelAdmin):
    list_display = ("session_datetime", "status", "student_name", "teacher_name", "college", "academic_year")
    search_fields = ("student_name", "teacher_name", "objective", "location")

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


