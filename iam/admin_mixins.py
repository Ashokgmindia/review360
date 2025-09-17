"""
Admin mixins for common functionality across different admin classes.
"""

from django.db import models
from django.contrib import admin


class CollegeScopedAdminMixin:
    """
    Mixin for admin classes that need college-based scoping.
    Provides common functionality for filtering querysets and forms.
    """
    
    def get_user_college_ids(self, request):
        """Get the college IDs that the current user has access to."""
        if getattr(request.user, "role", None) == "superadmin":
            return None  # Superadmin can access all colleges
        
        college_ids = []
        try:
            college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
        except Exception:
            college_ids = []
        if request.user.college_id:
            college_ids.append(request.user.college_id)
        return list({cid for cid in college_ids if cid})
    
    def get_queryset(self, request):
        """Filter queryset based on user's college access."""
        qs = super().get_queryset(request)
        college_ids = self.get_user_college_ids(request)
        
        if college_ids is None:  # Superadmin
            return qs
        elif college_ids:  # College admin with colleges
            return qs.filter(college_id__in=college_ids)
        else:  # No college access
            return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        """Filter form fields based on user's college access."""
        form = super().get_form(request, obj, **kwargs)
        college_ids = self.get_user_college_ids(request)
        
        if college_ids:  # Only filter for college admins
            self._filter_form_fields(form, college_ids)
        
        return form
    
    def _filter_form_fields(self, form, college_ids):
        """Filter form fields based on college IDs."""
        # Filter college field
        if 'college' in form.base_fields:
            from iam.models import College
            form.base_fields['college'].queryset = College.objects.filter(id__in=college_ids)
        
        # Filter user field (for teacher admin)
        if 'user' in form.base_fields:
            from iam.models import User
            form.base_fields['user'].queryset = User.objects.filter(
                models.Q(college_id__in=college_ids) | models.Q(colleges__in=college_ids)
            ).distinct()
        
        # Filter teacher field (for class admin)
        if 'teacher' in form.base_fields:
            from iam.models import User
            form.base_fields['teacher'].queryset = User.objects.filter(
                models.Q(college_id__in=college_ids) | models.Q(colleges__in=college_ids),
                role=User.Role.TEACHER
            ).distinct()
        
        # Filter class_ref field (for student admin)
        if 'class_ref' in form.base_fields:
            from academics.models import Class
            form.base_fields['class_ref'].queryset = Class.objects.filter(college_id__in=college_ids)
        
        # Filter department field
        if 'department' in form.base_fields:
            from academics.models import Department
            form.base_fields['department'].queryset = Department.objects.filter(college_id__in=college_ids)
    
    def save_model(self, request, obj, form, change):
        """Auto-assign college for college admins when creating new objects."""
        if not change and getattr(request.user, "role", None) == "college_admin":
            if request.user.college_id and not obj.college_id:
                obj.college = request.user.college
        super().save_model(request, obj, form, change)
