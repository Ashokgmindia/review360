from django.db import models
from django.utils import timezone


class ActivitySheet(models.Model):
    SHEET_TYPES = (
        ("ADOC", "ADOC"),
        ("DRCV", "DRCV"),
        ("OTHER", "OTHER"),
    )
    STATUS_CHOICES = (
        ("not_started", "not_started"),
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("validated", "validated"),
    )

    # For SaaS multi-tenant: tie to college and student
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="activity_sheets")
    student = models.ForeignKey("academics.Student", on_delete=models.CASCADE, related_name="activity_sheets", null=True, blank=True)
    student_name = models.CharField(max_length=200)
    sheet_type = models.CharField(max_length=20, choices=SHEET_TYPES)
    sheet_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True, default="")
    context = models.TextField(blank=True, default="")
    objectives = models.TextField(blank=True, default="")
    methodology = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    final_grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    academic_year = models.CharField(max_length=9)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.student_name} - {self.sheet_type} {self.sheet_number}"

    class Meta:
        unique_together = ("college", "student_name", "sheet_type", "sheet_number", "academic_year")
        indexes = [
            models.Index(fields=['college', 'academic_year']),
            models.Index(fields=['student', 'sheet_type']),
            models.Index(fields=['status']),
        ]


class Validation(models.Model):
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="validations")
    activity_sheet = models.ForeignKey(ActivitySheet, on_delete=models.CASCADE, related_name="validations")
    teacher = models.ForeignKey("academics.Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="validations")
    has_subject = models.BooleanField(default=False)
    context_well_formulated = models.BooleanField(default=False)
    objectives_validated = models.BooleanField(default=False)
    methodology_respected = models.BooleanField(default=False)
    session_grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    comments = models.TextField(blank=True, default="")
    validation_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Validation for {self.activity_sheet} by {self.teacher}"

    class Meta:
        unique_together = ("activity_sheet", "teacher")
        indexes = [
            models.Index(fields=['college', 'validation_date']),
            models.Index(fields=['activity_sheet']),
            models.Index(fields=['teacher']),
        ]


