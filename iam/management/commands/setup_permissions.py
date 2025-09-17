"""
Management command to set up permissions and groups for the Review360 application.

Usage:
    python manage.py setup_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from iam.permissions import create_permission_groups


class Command(BaseCommand):
    help = 'Set up permissions and groups for Review360 application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up permissions and groups...')
        
        # Create permission groups
        create_permission_groups()
        
        # Create custom permissions if needed
        self.create_custom_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up permissions and groups!')
        )

    def create_custom_permissions(self):
        """Create custom permissions for specific business logic."""
        from academics.models import Student, Teacher, Class, Department, Subject
        from learning.models import ActivitySheet, Validation
        from followup.models import FollowUpSession
        
        models_with_custom_perms = [
            (Student, [
                ('can_import_students', 'Can import student data'),
                ('can_export_students', 'Can export student data'),
            ]),
            (Teacher, [
                ('can_manage_own_profile', 'Can manage own teacher profile'),
                ('can_view_all_teachers', 'Can view all teachers in college'),
            ]),
            (Class, [
                ('can_assign_teacher', 'Can assign teacher to class'),
                ('can_manage_schedule', 'Can manage class schedule'),
            ]),
            (ActivitySheet, [
                ('can_validate_sheets', 'Can validate activity sheets'),
                ('can_grade_sheets', 'Can grade activity sheets'),
            ]),
            (FollowUpSession, [
                ('can_schedule_sessions', 'Can schedule follow-up sessions'),
                ('can_reschedule_sessions', 'Can reschedule follow-up sessions'),
            ]),
        ]
        
        for model, permissions in models_with_custom_perms:
            content_type = ContentType.objects.get_for_model(model)
            for codename, name in permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    name=name,
                    content_type=content_type,
                )
                if created:
                    self.stdout.write(f'Created permission: {name}')
                else:
                    self.stdout.write(f'Permission already exists: {name}')
