from django.db import models
from django.conf import settings
from django.utils import timezone


class Class(models.Model):
    name = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="classes")
    teacher = models.ForeignKey("Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="teaching_classes")
    section = models.CharField(max_length=10, blank=True, default="")
    program = models.CharField(max_length=100, blank=True, default="")
    semester = models.IntegerField(null=True, blank=True)
    room_number = models.CharField(max_length=20, blank=True, default="")
    max_students = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        indexes = [
            models.Index(fields=['college', 'academic_year']),
            models.Index(fields=['teacher', 'academic_year']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.academic_year})"


class Student(models.Model):
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, default="")
    address = models.TextField(blank=True, default="")
    profile_photo = models.ImageField(upload_to="student_photos/", null=True, blank=True)
    
    # Academic Information
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="students")
    academic_year = models.CharField(max_length=9)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="students")
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    student_number = models.CharField(max_length=30)
    admission_date = models.DateField(null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[
            ("enrolled", "Enrolled"),
            ("graduated", "Graduated"),
            ("dropped", "Dropped")
        ], 
        default="enrolled"
    )
    
    # Guardian Information
    guardian_name = models.CharField(max_length=100, blank=True, default="")
    guardian_contact = models.CharField(max_length=20, blank=True, default="")
    
    # System Fields
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ("college", "student_number")
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['class_ref', 'academic_year']),
            models.Index(fields=['department', 'academic_year']),
            models.Index(fields=['student_number']),
            models.Index(fields=['email']),
        ]




class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="departments")
    hod = models.ForeignKey("Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="head_of_departments")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("college", "code")
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.code})"


class Topic(models.Model):
    """Topics within a subject."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="topics")
    order = models.PositiveIntegerField(default=0, help_text="Order of the topic within the subject")
    is_active = models.BooleanField(default=True)
    
    # System Fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} - {self.subject.name}"

    class Meta:
        ordering = ['order', 'name']
        unique_together = ("subject", "name")
        indexes = [
            models.Index(fields=['subject', 'order']),
            models.Index(fields=['subject', 'is_active']),
        ]


class Subject(models.Model):
    # Basic Information
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True, default="")
    
    # Academic Structure
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="subjects")
    semester = models.IntegerField(null=True, blank=True)
    credits = models.IntegerField(default=0)
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Curriculum Resources
    syllabus_file = models.FileField(upload_to="syllabus/", null=True, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.code})"

    class Meta:
        unique_together = ("college", "code")
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['department', 'semester']),
            models.Index(fields=['code']),
        ]


class Teacher(models.Model):
    # User Account & Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="teachers")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, default="")
    emergency_contact = models.CharField(max_length=20, blank=True, default="")
    gender = models.CharField(max_length=10, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, default="")
    address = models.TextField(blank=True, default="")
    profile_photo = models.ImageField(upload_to="teacher_photos/", null=True, blank=True)
    
    # Employment Information
    employee_id = models.CharField(max_length=50, blank=True, default="")
    date_of_joining = models.DateField(null=True, blank=True)
    employment_type = models.CharField(
        max_length=50, 
        choices=[
            ("full-time", "Full-Time"),
            ("part-time", "Part-Time"),
            ("visiting", "Visiting")
        ], 
        blank=True,
        default=""
    )
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Academic & Administrative Roles
    designation = models.CharField(max_length=100, blank=True, default="")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="teachers")
    role_type = models.CharField(max_length=50, blank=True, default="Teaching")
    is_hod = models.BooleanField(default=False)
    reporting_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")
    
    # Qualifications & Experience
    highest_qualification = models.CharField(max_length=100, blank=True, default="")
    specialization = models.CharField(max_length=100, blank=True, default="")
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    subjects_handled = models.ManyToManyField(Subject, blank=True, related_name="teachers")
    research_publications = models.IntegerField(null=True, blank=True)
    certifications = models.TextField(blank=True, default="")
    resume = models.FileField(upload_to="teacher_cv/", null=True, blank=True)
    
    # Leave Management
    leaves_remaining = models.IntegerField(null=True, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        if self.employee_id:
            return f"{self.first_name} {self.last_name} ({self.employee_id})"
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['employee_id']),
        ]

    
    
    
    
    
    
    
    
    

