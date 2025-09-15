from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    user = models.ForeignKey("iam.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="audit_logs")
    table_name = models.CharField(max_length=50)
    record_id = models.BigIntegerField()
    action = models.CharField(max_length=20)
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)


class ArchiveRecord(models.Model):
    college = models.ForeignKey("iam.College", on_delete=models.CASCADE, related_name="archive_records")
    table_name = models.CharField(max_length=50)
    original_id = models.BigIntegerField()
    archived_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField()


