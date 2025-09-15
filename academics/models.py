from django.db import models
from django.conf import settings
from django.utils import timezone


class Class(models.Model):
    name = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="classes", null=True, blank=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="teaching_classes")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.academic_year})"


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="students")
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="students", null=True, blank=True)
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    student_number = models.CharField(max_length=30, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.first_name} {self.last_name}"


class ImportLog(models.Model):
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="import_logs")
    filename = models.CharField(max_length=255)
    imported_count = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    error_details = models.JSONField(blank=True, null=True)
    imported_at = models.DateTimeField(default=timezone.now)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="import_logs", null=True, blank=True)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="imports")




class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="departments")
    hod = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="head_of_departments")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("college", "code")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.code})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="subjects")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("college", "code")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.code})"


class Teacher(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="teachers")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, default="")
    gender = models.CharField(max_length=10, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, default="")
    profile_photo = models.ImageField(upload_to="teacher_photos/", null=True, blank=True)
    employee_id = models.CharField(max_length=50)
    date_of_joining = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


    designation = models.CharField(max_length=100, blank=True, default="")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="teachers")
    role_type = models.CharField(max_length=50, blank=True, default="Teaching")
    is_hod = models.BooleanField(default=False)
    reporting_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports")

    highest_qualification = models.CharField(max_length=100, blank=True, default="")
    specialization = models.CharField(max_length=100, blank=True, default="")
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    subjects_handled = models.ManyToManyField(Subject, blank=True, related_name="teachers")
    research_publications = models.IntegerField(default=0)
    certifications = models.TextField(blank=True, default="")
    resume = models.FileField(upload_to="teacher_cv/", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("college", "employee_id")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.first_name} {self.last_name}"

