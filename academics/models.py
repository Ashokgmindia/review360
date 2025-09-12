from django.db import models


class Class(models.Model):
    name = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.academic_year})"


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="students")
    academic_year = models.CharField(max_length=9)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.first_name} {self.last_name}"


class ImportLog(models.Model):
    class_ref = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="import_logs")
    filename = models.CharField(max_length=255)
    imported_count = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    error_details = models.JSONField(blank=True, null=True)
    imported_at = models.DateTimeField(auto_now_add=True)


