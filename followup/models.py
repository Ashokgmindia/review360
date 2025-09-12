from django.db import models


class FollowUpSession(models.Model):
    STATUS_CHOICES = (
        ("scheduled", "scheduled"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("rescheduled", "rescheduled"),
    )

    student_name = models.CharField(max_length=200)
    activity_sheet_title = models.CharField(max_length=255, blank=True, default="")
    teacher_name = models.CharField(max_length=200, blank=True, default="")
    session_datetime = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, default="")
    objective = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    google_calendar_event_id = models.CharField(max_length=255, blank=True, default="")
    academic_year = models.CharField(max_length=9)
    created_at = models.DateTimeField(auto_now_add=True)



