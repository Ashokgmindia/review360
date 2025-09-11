from django.contrib import admin
from .models import College


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
