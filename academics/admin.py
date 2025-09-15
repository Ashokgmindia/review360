from django.contrib import admin
from iam.models import User

from .models import Department, Subject, Teacher, Class, Student, ImportLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "college", "hod")
    search_fields = ("name", "code")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "college")
    search_fields = ("name", "code")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "employee_id", "college", "department", "is_active")
    search_fields = ("first_name", "last_name", "email", "employee_id")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "college", "teacher")
    search_fields = ("name", "academic_year")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "student_number", "college", "class_ref", "department", "academic_year", "is_active")
    search_fields = ("first_name", "last_name", "student_number", "email")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "class_ref", "imported_count", "errors_count", "imported_at")
    search_fields = ("filename",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            return qs.filter(college_id=request.user.college_id)
        return qs.none()


