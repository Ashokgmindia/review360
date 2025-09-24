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
    max_students = models.PositiveIntegerField(default=0, null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
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
    # User Account & Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile", null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, default="")
    address = models.TextField(blank=True, default="")
    profile_photo = models.ImageField(upload_to="student_photos/", null=True, blank=True)
    
    # Academic Information
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    academic_year = models.CharField(max_length=9, blank=True, null=True)
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="students", null=True, blank=True)
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    student_number = models.CharField(max_length=30, blank=True, null=True)
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
        # Remove unique_together constraint since college and student_number are now optional
        # unique_together = ("college", "student_number")
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
    subjects_handled = models.ManyToManyField("learning.Subject", blank=True, related_name="teachers")
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


class StudentSubject(models.Model):
    """Model to track subject assignments to students with teacher information."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="assigned_subjects")
    subject = models.ForeignKey("learning.Subject", on_delete=models.CASCADE, related_name="assigned_students")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="teaching_assignments")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="student_subject_assignments")
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "subject", "class_ref")
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['class_ref', 'is_active']),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.student} - {self.subject} ({self.teacher})"


class StudentTopicProgress(models.Model):
    """Model to track individual student progress on specific topics."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('validated', 'Validated'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="topic_progress")
    topic = models.ForeignKey("learning.Topic", on_delete=models.CASCADE, related_name="student_progress")
    subject = models.ForeignKey("learning.Subject", on_delete=models.CASCADE, related_name="student_topic_progress")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="student_topic_progress")
    
    # Student-specific progress fields
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='not_started',
        help_text="Student's current status on this topic"
    )
    grade = models.PositiveIntegerField(
        default=0, 
        help_text="Student's grade for this topic (0-10 scale)"
    )
    comments_and_recommendations = models.TextField(
        blank=True, 
        default="", 
        help_text="Comments and recommendations about the student's progress on this topic"
    )
    
    # Question fields (student-specific)
    qns1_text = models.TextField(blank=True, default="", help_text="Question 1 text")
    qns1_checked = models.BooleanField(default=False, help_text="Question 1 checkbox")
    qns2_text = models.TextField(blank=True, default="", help_text="Question 2 text")
    qns2_checked = models.BooleanField(default=False, help_text="Question 2 checkbox")
    qns3_text = models.TextField(blank=True, default="", help_text="Question 3 text")
    qns3_checked = models.BooleanField(default=False, help_text="Question 3 checkbox")
    qns4_text = models.TextField(blank=True, default="", help_text="Question 4 text")
    qns4_checked = models.BooleanField(default=False, help_text="Question 4 checkbox")
    
    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "topic", "class_ref")
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['topic', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
            models.Index(fields=['class_ref', 'is_active']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.student} - {self.topic.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to automatically update status based on grade."""
        # Update status based on grade
        if self.grade >= 7:
            self.status = 'validated'
        elif self.grade > 0:
            self.status = 'in_progress'
        else:
            self.status = 'not_started'
        super().save(*args, **kwargs)

    
    
    
    
    
    
    
    
    

