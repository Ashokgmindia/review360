from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student_name", "sheet_type", "sheet_number", "academic_year")


class Validation(models.Model):
    activity_sheet = models.ForeignKey(ActivitySheet, on_delete=models.CASCADE, related_name="validations")
    has_subject = models.BooleanField(default=False)
    context_well_formulated = models.BooleanField(default=False)
    objectives_validated = models.BooleanField(default=False)
    methodology_respected = models.BooleanField(default=False)
    session_grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    comments = models.TextField(blank=True, default="")
    validation_date = models.DateTimeField(auto_now_add=True)


