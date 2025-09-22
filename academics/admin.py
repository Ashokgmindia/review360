from django.contrib import admin
from django.db import models
from django import forms
from django.core.exceptions import ValidationError
from iam.models import User

from .models import Department, Teacher, Class, Student


class ClassAdminForm(forms.ModelForm):
    """Custom form for Class admin with student file upload."""
    student_file = forms.FileField(
        required=False,
        help_text="Upload Excel, CSV, or JSON file containing student data. Students will be automatically assigned to this class.",
        widget=forms.FileInput(attrs={'accept': '.xlsx,.csv,.json'})
    )
    
    class Meta:
        model = Class
        fields = '__all__'
        widgets = {
            'student_file': forms.FileInput(attrs={'accept': '.xlsx,.csv,.json'})
        }
    
    def clean_student_file(self):
        file = self.cleaned_data.get('student_file')
        if file:
            # Validate file extension
            allowed_extensions = ['.xlsx', '.csv', '.json']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError(f"File type not supported. Please upload Excel (.xlsx), CSV (.csv), or JSON (.json) files.")
        return file


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
    form = ClassAdminForm
    list_display = ("name", "section", "program", "semester", "academic_year", "room_number", "max_students", "college", "teacher")
    search_fields = ("name", "academic_year", "section", "program", "room_number")
    fields = ("name", "academic_year", "is_active", "college", "teacher", "section", "program", "semester", "room_number", "max_students", "student_file", "metadata")

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
        
        # Save the class first
        super().save_model(request, obj, form, change)
        
        # Handle student file upload if provided
        student_file = form.cleaned_data.get('student_file')
        if student_file and not change:  # Only process file upload when creating new class
            try:
                from .bulk_upload_utils import process_student_bulk_upload, BulkUploadError
                
                # Process student bulk upload
                result = process_student_bulk_upload(student_file, obj.college, request.user)
                
                # Store upload results in class metadata for reference
                obj.metadata = {
                    'student_upload_result': {
                        'success_count': result['success_count'],
                        'error_count': result['error_count'],
                        'errors': result['errors']
                    }
                }
                obj.save()
                
                # Assign successfully created students to this class
                if result['success_count'] > 0:
                    # Get the students created in this batch (most recent ones without class assignment)
                    students_to_assign = Student.objects.filter(
                        college=obj.college,
                        class_ref__isnull=True
                    ).order_by('-created_at')[:result['success_count']]
                    
                    # Assign students to this class
                    for student in students_to_assign:
                        student.class_ref = obj
                        student.save()
                    
                    # Update metadata with assignment info
                    obj.metadata['student_upload_result']['assigned_to_class'] = students_to_assign.count()
                    obj.save()
                
            except BulkUploadError as e:
                # If student upload fails, still create the class but add error to metadata
                obj.metadata = {
                    'student_upload_error': str(e)
                }
                obj.save()
            except Exception as e:
                # If any other error occurs, still create the class
                obj.metadata = {
                    'student_upload_error': f"Unexpected error: {str(e)}"
                }
                obj.save()


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




