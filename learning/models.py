from django.db import models
from django.utils import timezone


class Subject(models.Model):
    # Basic Information
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True, default="")
    
    # Academic Structure
    department = models.ForeignKey("academics.Department", on_delete=models.CASCADE, related_name="subjects")
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


class Topic(models.Model):
    """Topics within a subject."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('validated', 'Validated'),
    ]
    
    name = models.CharField(max_length=200)
    context = models.TextField(blank=True, default="", help_text="Context or background information for the topic")
    objectives = models.TextField(blank=True, default="", help_text="Learning objectives for this topic")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='not_started',
        help_text="Current status of the topic"
    )
    grade = models.PositiveIntegerField(
        default=0, 
        help_text="Grade for the topic (0-10 scale)"
    )
    comments_and_recommendations = models.TextField(blank=True, default="", help_text="Comments and recommendations about the topic")
    
    # Question fields (text + checkbox)
    qns1_text = models.TextField(blank=True, default="", help_text="Question 1 text")
    qns1_checked = models.BooleanField(default=False, help_text="Question 1 checkbox")
    qns2_text = models.TextField(blank=True, default="", help_text="Question 2 text")
    qns2_checked = models.BooleanField(default=False, help_text="Question 2 checkbox")
    qns3_text = models.TextField(blank=True, default="", help_text="Question 3 text")
    qns3_checked = models.BooleanField(default=False, help_text="Question 3 checkbox")
    qns4_text = models.TextField(blank=True, default="", help_text="Question 4 text")
    qns4_checked = models.BooleanField(default=False, help_text="Question 4 checkbox")
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    is_active = models.BooleanField(default=True)
    
    # System Fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Model-level validation (no request context available here)."""
        # Validation is handled at serializer level where request context is available
        pass
    
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

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} - {self.subject.name}"

    class Meta:
        ordering = ['name']
        unique_together = ("subject", "name")
        indexes = [
            models.Index(fields=['subject', 'is_active']),
        ]


