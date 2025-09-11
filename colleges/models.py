from django.db import models

# Create your models here.

class College(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, default="")
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)