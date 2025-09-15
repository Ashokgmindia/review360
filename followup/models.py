from django.db import models
from django.utils import timezone


class FollowUpSession(models.Model):
    STATUS_CHOICES = (
        ("scheduled", "scheduled"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("rescheduled", "rescheduled"),
    )

    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="follow_up_sessions", null=True, blank=True)
    student = models.ForeignKey("academics.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    activity_sheet = models.ForeignKey("learning.ActivitySheet", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    teacher = models.ForeignKey("iam.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_up_sessions")
    student_name = models.CharField(max_length=200)
    activity_sheet_title = models.CharField(max_length=255, blank=True, default="")
    teacher_name = models.CharField(max_length=200, blank=True, default="")
    session_datetime = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, default="")
    objective = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    google_calendar_event_id = models.CharField(max_length=255, blank=True, default="")
    academic_year = models.CharField(max_length=9)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)



