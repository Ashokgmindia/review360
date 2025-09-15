from django.contrib import admin
from django.db import models
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, College


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("username", "email", "role", "colleges_display", "is_staff", "is_superuser")
    list_filter = ("role", "college", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number")} ),
        # Do not allow editing college directly from user form; it's derived from College.admin
        ("IAM", {"fields": ("role", "employee_id", "designation")} ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")} ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                # Hide college on add; it will be linked automatically when setting College.admin
                "fields": ("username", "email", "first_name", "last_name", "phone_number", "role", "password1", "password2"),
            },
        ),
    )

    # Scope visibility to the current user's college(s) when they are a college admin
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return qs
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = []
            try:
                college_ids = list(request.user.colleges.values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            if college_ids:
                # show users whose FK college is any of admin's colleges OR
                # users who are members via M2M of any admin colleges
                return qs.filter(models.Q(college_id__in=college_ids) | models.Q(colleges__in=college_ids)).distinct()
        # Other roles: see nothing
        return qs.none()

    def has_add_permission(self, request):
        # Superadmins can add; college admins can add users for their own college only (enforced in save_model)
        if getattr(request.user, "role", None) in (User.Role.SUPERADMIN, User.Role.COLLEGE_ADMIN):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return True
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if obj is None:
                return True
            user_college_ids = []
            try:
                user_college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if request.user.college_id:
                user_college_ids.append(request.user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            return obj.college_id in user_college_ids
        return False

    def has_delete_permission(self, request, obj=None):
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return True
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if obj is None:
                return True
            user_college_ids = []
            try:
                user_college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if request.user.college_id:
                user_college_ids.append(request.user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            return obj.college_id in user_college_ids
        return False

    def has_view_permission(self, request, obj=None):
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return True
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if obj is None:
                return True
            user_college_ids = []
            try:
                user_college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if request.user.college_id:
                user_college_ids.append(request.user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            return obj.college_id in user_college_ids
        return False

    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        # Ensure the app and model appear for college admins
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            perms["view"] = True
        return perms

    def save_model(self, request, obj, form, change):
        # When a college admin creates a user, force the user's college to the admin's college
        if not change and getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN and request.user.college_id:
            obj.college_id = request.user.college_id
            # Enforce RBAC restrictions
            if obj.role == User.Role.SUPERADMIN:
                obj.role = User.Role.STUDENT
            obj.is_superuser = False
            obj.is_staff = False
        super().save_model(request, obj, form, change)
        # Keep M2M membership in sync with FK for convenience
        try:
            if obj.college_id:
                obj.colleges.add(obj.college)
        except Exception:
            pass

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Limit role choices for college admins
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if "role" in form.base_fields:
                allowed = [User.Role.TEACHER, User.Role.STUDENT, User.Role.COLLEGE_ADMIN]
                form.base_fields["role"].choices = [
                    (value, label)
                    for value, label in User.Role.choices
                    if value in allowed and value != User.Role.SUPERADMIN
                ]
            # Hide staff/superuser/groups permissions
            for field in ("is_superuser", "is_staff", "groups", "user_permissions"):
                if field in form.base_fields:
                    form.base_fields[field].disabled = True
                    form.base_fields[field].required = False
        return form

    def college_display(self, obj):
        if not obj.college:
            return "-"
        if obj.college.name and obj.college.code:
            return f"{obj.college.name} ({obj.college.code})"
        return str(obj.college)
    college_display.short_description = "College"

    def colleges_display(self, obj):
        try:
            items = list(obj.colleges.values_list("name", "code"))
        except Exception:
            items = []
        # Avoid double showing FK college if present in M2M
        seen = set()
        parts = []
        if obj.college_id:
            key = (obj.college.name, obj.college.code)
            seen.add(key)
            parts.append(self.college_display(obj))
        for name, code in items:
            key = (name, code)
            if key in seen:
                continue
            if name and code:
                parts.append(f"{name} ({code})")
            else:
                parts.append(name or code or "-")
        return ", ".join(parts) or "-"
    colleges_display.short_description = "Colleges"


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "address", "contact_email", "contact_phone")

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
                return qs.filter(id__in=college_ids)
        return qs.none()

    def has_add_permission(self, request):
        # Only superadmins can add colleges via admin
        return getattr(request.user, "role", None) == User.Role.SUPERADMIN

    def has_change_permission(self, request, obj=None):
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return True
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if obj is None:
                return True
            user_college_ids = []
            try:
                user_college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if request.user.college_id:
                user_college_ids.append(request.user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            return obj and obj.id in user_college_ids
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superadmins can delete colleges
        return getattr(request.user, "role", None) == User.Role.SUPERADMIN

    def has_view_permission(self, request, obj=None):
        if getattr(request.user, "role", None) == User.Role.SUPERADMIN:
            return True
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if obj is None:
                return True
            user_college_ids = []
            try:
                user_college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                user_college_ids = []
            if request.user.college_id:
                user_college_ids.append(request.user.college_id)
            user_college_ids = list({cid for cid in user_college_ids if cid})
            return obj and obj.id in user_college_ids
        return False

    def get_model_perms(self, request):
        perms = super().get_model_perms(request)
        # Ensure the app and model appear for college admins
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            perms["view"] = True
        return perms

    def save_model(self, request, obj, form, change):
        # Save the college first
        super().save_model(request, obj, form, change)
        # Ensure selected admin has proper role and is linked via M2M to this college
        try:
            admin_user = obj.admin
            if admin_user is not None:
                if getattr(admin_user, "role", None) != User.Role.SUPERADMIN:
                    admin_user.role = User.Role.COLLEGE_ADMIN
                if not admin_user.college_id:
                    admin_user.college = obj
                admin_user.save()
                try:
                    admin_user.colleges.add(obj)
                except Exception:
                    pass
        except Exception:
            pass


