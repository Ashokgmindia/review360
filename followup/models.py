from django.db import models
from django.utils import timezone


class Location(models.Model):
    """Model to store predefined locations for follow-up sessions."""
    name = models.CharField(max_length=255, help_text="Name of the location (e.g., 'Classroom A', 'Library', 'Online')")
    description = models.TextField(blank=True, default="", help_text="Description of the location")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="followup_locations")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.college.name})"

    class Meta:
        unique_together = ("college", "name")
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['name']),
        ]


class Objective(models.Model):
    """Model to store predefined objectives for follow-up sessions."""
    title = models.CharField(max_length=255, help_text="Title of the objective")
    description = models.TextField(help_text="Detailed description of the objective")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="followup_objectives")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} ({self.college.name})"

    class Meta:
        indexes = [
            models.Index(fields=['college', 'is_active']),
            models.Index(fields=['title']),
        ]


class FollowUpSession(models.Model):
    STATUS_CHOICES = (
        ("scheduled", "scheduled"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("rescheduled", "rescheduled"),
    )

    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="follow_up_sessions")
    student = models.ForeignKey("academics.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    subject = models.ForeignKey("learning.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    topic = models.ForeignKey("learning.Topic", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    teacher = models.ForeignKey("academics.Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    objective = models.ForeignKey("Objective", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    student_name = models.CharField(max_length=200)
    subject_name = models.CharField(max_length=255, blank=True, default="")
    topic_name = models.CharField(max_length=255, blank=True, default="")
    teacher_name = models.CharField(max_length=200, blank=True, default="")
    location_name = models.CharField(max_length=255, blank=True, default="")
    objective_title = models.CharField(max_length=255, blank=True, default="")
    session_datetime = models.DateTimeField()
    notes_for_student = models.TextField(blank=True, default="", help_text="Notes or instructions for the student")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    google_calendar_event_id = models.CharField(max_length=255, blank=True, default="")
    add_to_google_calendar = models.BooleanField(default=False, help_text="Whether to add this session to Google Calendar")
    invite_student = models.BooleanField(default=False, help_text="Whether to send email invitation to student")
    automatic_reminder = models.BooleanField(default=False, help_text="Whether to send automatic reminder 24 hours in advance")
    academic_year = models.CharField(max_length=9, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.student_name} - {self.session_datetime.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        indexes = [
            models.Index(fields=['college', 'academic_year']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['teacher', 'session_datetime']),
            models.Index(fields=['status']),
        ]



