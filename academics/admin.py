from django.contrib import admin
from django.db import models
from iam.models import User

from .models import Department, Subject, Teacher, Class, Student, Topic


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "college", "hod")
    search_fields = ("name", "code")

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


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "college")
    search_fields = ("name", "code")

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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "employee_id", "college", "department", "is_active")
    search_fields = ("first_name", "last_name", "email", "employee_id")
    exclude = ("user",)  # Hide the user field from the form

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filter foreign key fields based on user's college context
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            # Get user's college IDs
            college_ids = []
            try:
                college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            
            if college_ids:
                # Filter college field
                if 'college' in form.base_fields:
                    from iam.models import College
                    form.base_fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter department field
                if 'department' in form.base_fields:
                    from .models import Department
                    form.base_fields['department'].queryset = Department.objects.filter(college_id__in=college_ids)
        
        return form

    def save_model(self, request, obj, form, change):
        from django.db import transaction
        
        if not change:  # Creating new teacher
            # Auto-assign college for college admins
            if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
                if request.user.college_id and not obj.college_id:
                    obj.college = request.user.college
            
            # Create a new user account for the teacher
            with transaction.atomic():
                # Generate username from email
                username = obj.email
                
                # Check if user already exists
                if User.objects.filter(email=obj.email).exists():
                    raise ValueError(f"A user with email {obj.email} already exists.")
                
                # Create the user
                user = User.objects.create_user(
                    username=username,
                    email=obj.email,
                    password='temp_password_123',  # Temporary password
                    role=User.Role.TEACHER,
                    college=obj.college,
                    first_name=obj.first_name,
                    last_name=obj.last_name,
                    phone_number=obj.phone_number,
                )
                
                # Add user to college's member users
                if obj.college:
                    user.colleges.add(obj.college)
                
                # Link the teacher to the user
                obj.user = user
                
                # Save the teacher
                super().save_model(request, obj, form, change)
        else:
            # Updating existing teacher
            super().save_model(request, obj, form, change)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "program", "semester", "academic_year", "room_number", "max_students", "college", "teacher")
    search_fields = ("name", "academic_year", "section", "program", "room_number")

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filter foreign key fields based on user's college context
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            # Get user's college IDs
            college_ids = []
            try:
                college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            
            if college_ids:
                # Filter college field
                if 'college' in form.base_fields:
                    from iam.models import College
                    form.base_fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter teacher field to only show teachers from the same college
                if 'teacher' in form.base_fields:
                    from .models import Teacher
                    form.base_fields['teacher'].queryset = Teacher.objects.filter(college_id__in=college_ids)
        
        return form

    def save_model(self, request, obj, form, change):
        # Auto-assign college for college admins
        if not change and getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if request.user.college_id and not obj.college_id:
                obj.college = request.user.college
        super().save_model(request, obj, form, change)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "student_number", "college", "class_ref", "department", "academic_year", "is_active")
    search_fields = ("first_name", "last_name", "student_number", "email")

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filter foreign key fields based on user's college context
        if getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            # Get user's college IDs
            college_ids = []
            try:
                college_ids = list(getattr(request.user, "colleges").values_list("id", flat=True))
            except Exception:
                college_ids = []
            if request.user.college_id:
                college_ids.append(request.user.college_id)
            college_ids = list({cid for cid in college_ids if cid})
            
            if college_ids:
                # Filter college field
                if 'college' in form.base_fields:
                    from iam.models import College
                    form.base_fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter class_ref field to only show classes from the same college
                if 'class_ref' in form.base_fields:
                    form.base_fields['class_ref'].queryset = Class.objects.filter(college_id__in=college_ids)
                
                # Filter department field
                if 'department' in form.base_fields:
                    form.base_fields['department'].queryset = Department.objects.filter(college_id__in=college_ids)
        
        return form

    def save_model(self, request, obj, form, change):
        # Auto-assign college for college admins
        if not change and getattr(request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            if request.user.college_id and not obj.college_id:
                obj.college = request.user.college
        super().save_model(request, obj, form, change)


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
    
    def clean(self):
        """Admin-level validation (no request context available here)."""
        # Validation is handled at serializer level where request context is available
        pass


