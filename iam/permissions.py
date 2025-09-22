"""
Comprehensive permission system for Review360 multi-tenant SaaS application.

This module implements fine-grained, role-based permissions that map to the
permission matrix defined in the requirements document.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class RoleBasedPermission(BasePermission):
    """
    Role-based permission system that enforces the permission matrix.
    
    Roles:
    - SUPERADMIN: Full access to everything
    - COLLEGE_ADMIN: Full access within their college(s)
    - TEACHER: Limited access to their assigned classes/students
    - STUDENT: Read-only access to their own data
    """
    
    # Permission matrix mapping roles to allowed actions
    ROLE_PERMISSIONS = {
        'superadmin': {
            'academics': {
                'class': ['create', 'read', 'update', 'delete'],
                'student': ['create', 'read', 'update', 'delete'],
                'teacher': ['create', 'read', 'update', 'delete'],
                'department': ['create', 'read', 'update', 'delete'],
                'subject': ['create', 'read', 'update', 'delete'],
                'topic': ['create', 'read', 'update', 'delete'],
                'importlog': ['read'],
            },
            'learning': {
                'subject': ['create', 'read', 'update', 'delete'],
                'topic': ['create', 'read', 'update', 'delete'],
            },
            'followup': {
                'followupsession': ['create', 'read', 'update', 'delete'],
            },
            'compliance': {
                'auditlog': ['read'],
                'archiverecord': ['create', 'read', 'update', 'delete'],
            }
        },
        'college_admin': {
            'academics': {
                'class': ['create', 'read', 'update', 'delete'],
                'student': ['create', 'read', 'update', 'delete'],
                'teacher': ['create', 'read', 'update', 'delete'],
                'department': ['create', 'read', 'update', 'delete'],
                'subject': ['create', 'read', 'update', 'delete'],
                'topic': ['create', 'read', 'update', 'delete'],
                'importlog': ['read'],
            },
            'learning': {
                'subject': ['create', 'read', 'update', 'delete'],
                'topic': ['create', 'read', 'update', 'delete'],
            },
            'followup': {
                'followupsession': ['read', 'update', 'delete'],
            },
            'compliance': {
                'auditlog': ['read'],
                'archiverecord': ['read'],
            }
        },
        'teacher': {
            'academics': {
                'class': ['read'],
                'student': ['read', 'update'],  # Limited updates only
                'teacher': ['read', 'update'],  # Own profile only
                'department': ['read', 'update'],  # If HoD
                'subject': ['read', 'update'],  # Own subjects
                'topic': ['create', 'read', 'update', 'delete'],  # Topics for their subjects
                'importlog': ['create', 'read'],  # Own imports
            },
            'learning': {
                'subject': ['read', 'update'],  # Own subjects
                'topic': ['create', 'read', 'update', 'delete'],  # Topics for their subjects
            },
            'followup': {
                'followupsession': ['create', 'read', 'update', 'delete'],
            },
            'compliance': {
                'auditlog': [],
                'archiverecord': [],
            }
        },
        'student': {
            'academics': {
                'class': ['read'],
                'student': ['read', 'update'],  # Own profile only
                'teacher': ['read'],
                'department': ['read'],
                'subject': ['read'],
                'topic': ['read'],  # Read topics for subjects
                'importlog': [],
            },
            'learning': {
                'subject': ['read'],
                'topic': ['read'],
            },
            'followup': {
                'followupsession': ['read'],
            },
            'compliance': {
                'auditlog': [],
                'archiverecord': [],
            }
        }
    }
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            print("DEBUG RoleBasedPermission: User not authenticated")
            return False
            
        user_role = getattr(request.user, 'role', None)
        if not user_role:
            print("DEBUG RoleBasedPermission: No user role")
            return False
            
        # Superadmin has all permissions
        if user_role == 'superadmin':
            print("DEBUG RoleBasedPermission: Superadmin - ALLOWED")
            return True
            
        # Get the model name and action
        model_name = self._get_model_name(view)
        action = self._get_action_name(view)
        app_name = self._get_app_name(view)
        
        if not model_name or not action:
            return False
            
        # Check if user's role has permission for this action on this model
        role_perms = self.ROLE_PERMISSIONS.get(user_role, {})
        app_perms = role_perms.get(app_name, {})
        model_perms = app_perms.get(model_name, [])
        
        return action in model_perms
    
    def _get_app_name(self, view):
        """Extract app name from view."""
        # Try to get the model from the view's queryset
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model._meta.app_label
        
        # Fallback: try to get model from view class name
        if hasattr(view, '__class__'):
            class_name = view.__class__.__name__
            if class_name.endswith('ViewSet'):
                model_name = class_name[:-7].lower()  # Remove 'ViewSet' suffix
                # Map common viewset names to app names
                if model_name in ['department', 'class', 'student', 'teacher']:
                    return 'academics'
                elif model_name in ['topic', 'subject']:
                    return 'learning'
                elif model_name in ['followupsession']:
                    return 'followup'
                elif model_name in ['auditlog', 'archiverecord']:
                    return 'compliance'
        
        return None
    
    def _get_model_name(self, view):
        """Extract model name from view."""
        # Try to get the model from the view's queryset
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model._meta.model_name
        
        # Fallback: try to get model name from view class name
        if hasattr(view, '__class__'):
            class_name = view.__class__.__name__
            if class_name.endswith('ViewSet'):
                model_name = class_name[:-7].lower()  # Remove 'ViewSet' suffix
                return model_name
        
        return None
    
    def _get_action_name(self, view):
        """Map view action to permission action."""
        action_mapping = {
            'list': 'read',
            'retrieve': 'read',
            'create': 'create',
            'update': 'update',
            'partial_update': 'update',
            'destroy': 'delete',
        }
        return action_mapping.get(getattr(view, 'action', None), 'read')


class FieldLevelPermission(BasePermission):
    """
    Field-level permission system for fine-grained access control.
    
    This ensures users can only modify fields they have permission to change.
    """
    
    # Fields that students cannot modify
    STUDENT_READONLY_FIELDS = {
        'student': ['class_ref', 'academic_year', 'college', 'department', 'student_number', 'status'],
        'teacher': ['college', 'employee_id', 'department'],
        'class': ['college', 'academic_year'],
        'department': ['college'],
        'subject': ['college', 'department'],
    }
    
    # Fields that teachers cannot modify
    TEACHER_READONLY_FIELDS = {
        'student': ['class_ref', 'academic_year', 'college', 'department', 'student_number', 'status'],
        'teacher': ['college', 'employee_id'],
        'class': ['college', 'academic_year'],
        'department': ['college'],
        'subject': ['college', 'department'],
    }
    
    def has_permission(self, request, view):
        return True  # Field-level checks are done in serializers
    
    def has_object_permission(self, request, view, obj):
        """Check if user can modify specific fields of an object."""
        user_role = getattr(request.user, 'role', None)
        model_name = obj._meta.model_name
        
        if user_role == 'student':
            readonly_fields = self.STUDENT_READONLY_FIELDS.get(model_name, [])
        elif user_role == 'teacher':
            readonly_fields = self.TEACHER_READONLY_FIELDS.get(model_name, [])
        else:
            return True  # Admin roles have full access
            
        # Check if user is trying to modify readonly fields
        if hasattr(request, 'data'):
            for field in readonly_fields:
                if field in request.data:
                    return False
                    
        return True


class TenantScopedPermission(BasePermission):
    """
    Ensures users can only access data within their tenant scope.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            print("DEBUG TenantScopedPermission: User not authenticated")
            return False
            
        # Superadmin can access all tenants
        if getattr(request.user, 'role', None) == 'superadmin':
            print("DEBUG TenantScopedPermission: Superadmin - ALLOWED")
            return True
            
        # Other users must belong to at least one college
        user_colleges = list(request.user.colleges.values_list('id', flat=True))
        if request.user.college_id:
            user_colleges.append(request.user.college_id)
        
        return len(user_colleges) > 0


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the object
        return obj.user == request.user


def create_permission_groups():
    """
    Create Django permission groups for each role.
    This should be called during migrations or management commands.
    """
    from django.contrib.auth.models import Group
    
    # Define groups and their permissions
    groups_permissions = {
        'College Admins': [
            'academics.add_class',
            'academics.change_class',
            'academics.delete_class',
            'academics.view_class',
            'academics.add_student',
            'academics.change_student',
            'academics.delete_student',
            'academics.view_student',
            'academics.add_teacher',
            'academics.change_teacher',
            'academics.delete_teacher',
            'academics.view_teacher',
            'academics.add_department',
            'academics.change_department',
            'academics.delete_department',
            'academics.view_department',
            'academics.add_subject',
            'academics.change_subject',
            'academics.delete_subject',
            'academics.view_subject',
            'academics.add_topic',
            'academics.change_topic',
            'academics.delete_topic',
            'academics.view_topic',
            'academics.view_importlog',
            'learning.view_activitysheet',
            'learning.view_validation',
            'followup.change_followupsession',
            'followup.delete_followupsession',
            'followup.view_followupsession',
            'compliance.view_auditlog',
            'compliance.view_archiverecord',
        ],
        'Teachers': [
            'academics.view_class',
            'academics.change_student',
            'academics.view_student',
            'academics.change_teacher',
            'academics.view_teacher',
            'academics.view_department',
            'academics.change_department',  # If HoD
            'academics.view_subject',
            'academics.change_subject',  # Own subjects
            'academics.add_topic',
            'academics.change_topic',
            'academics.delete_topic',
            'academics.view_topic',
            'academics.add_importlog',
            'academics.view_importlog',
            'learning.add_activitysheet',
            'learning.change_activitysheet',
            'learning.view_activitysheet',
            'learning.add_validation',
            'learning.change_validation',
            'learning.view_validation',
            'followup.add_followupsession',
            'followup.change_followupsession',
            'followup.delete_followupsession',
            'followup.view_followupsession',
        ],
        'Students': [
            'academics.view_class',
            'academics.change_student',  # Own profile only
            'academics.view_student',
            'academics.view_teacher',
            'academics.view_department',
            'academics.view_subject',
            'academics.view_topic',
            'learning.add_activitysheet',
            'learning.change_activitysheet',
            'learning.view_activitysheet',
            'learning.view_validation',
            'followup.view_followupsession',
        ]
    }
    
    for group_name, permission_codenames in groups_permissions.items():
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            # Add permissions to the group
            permissions = Permission.objects.filter(codename__in=permission_codenames)
            group.permissions.set(permissions)
            print(f"Created group '{group_name}' with {permissions.count()} permissions")
        else:
            print(f"Group '{group_name}' already exists")
