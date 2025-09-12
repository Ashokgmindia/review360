from django.db import models


class AuditLog(models.Model):
    table_name = models.CharField(max_length=50)
    record_id = models.BigIntegerField()
    action = models.CharField(max_length=20)
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ArchiveRecord(models.Model):
    table_name = models.CharField(max_length=50)
    original_id = models.BigIntegerField()
    archived_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()


