"""
Custom forms for the academics app.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import Teacher, Class, Student, Department, Subject

User = get_user_model()


class TeacherForm(forms.ModelForm):
    """Custom form for Teacher model that handles user creation automatically."""
    
    class Meta:
        model = Teacher
        exclude = ('user',)  # Exclude user field as it will be created automatically
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter fields based on user's college context
        if self.request and getattr(self.request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = self._get_user_college_ids()
            if college_ids:
                # Filter college field
                if 'college' in self.fields:
                    from iam.models import College
                    self.fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter department field
                if 'department' in self.fields:
                    self.fields['department'].queryset = Department.objects.filter(college_id__in=college_ids)
    
    def _get_user_college_ids(self):
        """Get the college IDs that the current user has access to."""
        college_ids = []
        try:
            college_ids = list(getattr(self.request.user, "colleges").values_list("id", flat=True))
        except Exception:
            college_ids = []
        if self.request.user.college_id:
            college_ids.append(self.request.user.college_id)
        return list({cid for cid in college_ids if cid})
    
    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class ClassForm(forms.ModelForm):
    """Custom form for Class model with filtered teacher choices."""
    
    class Meta:
        model = Class
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter fields based on user's college context
        if self.request and getattr(self.request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = self._get_user_college_ids()
            if college_ids:
                # Filter college field
                if 'college' in self.fields:
                    from iam.models import College
                    self.fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter teacher field to only show teachers from the same college
                if 'teacher' in self.fields:
                    self.fields['teacher'].queryset = Teacher.objects.filter(college_id__in=college_ids)
    
    def _get_user_college_ids(self):
        """Get the college IDs that the current user has access to."""
        college_ids = []
        try:
            college_ids = list(getattr(self.request.user, "colleges").values_list("id", flat=True))
        except Exception:
            college_ids = []
        if self.request.user.college_id:
            college_ids.append(self.request.user.college_id)
        return list({cid for cid in college_ids if cid})


class StudentForm(forms.ModelForm):
    """Custom form for Student model with filtered choices."""
    
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'graduation_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter fields based on user's college context
        if self.request and getattr(self.request.user, "role", None) == User.Role.COLLEGE_ADMIN:
            college_ids = self._get_user_college_ids()
            if college_ids:
                # Filter college field
                if 'college' in self.fields:
                    from iam.models import College
                    self.fields['college'].queryset = College.objects.filter(id__in=college_ids)
                
                # Filter class_ref field to only show classes from the same college
                if 'class_ref' in self.fields:
                    self.fields['class_ref'].queryset = Class.objects.filter(college_id__in=college_ids)
                
                # Filter department field
                if 'department' in self.fields:
                    self.fields['department'].queryset = Department.objects.filter(college_id__in=college_ids)
    
    def _get_user_college_ids(self):
        """Get the college IDs that the current user has access to."""
        college_ids = []
        try:
            college_ids = list(getattr(self.request.user, "colleges").values_list("id", flat=True))
        except Exception:
            college_ids = []
        if self.request.user.college_id:
            college_ids.append(self.request.user.college_id)
        return list({cid for cid in college_ids if cid})
