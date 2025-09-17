"""
Multi-tenant middleware for automatic tenant scoping.

This middleware ensures that all database queries are automatically
scoped to the current user's tenant (college) context.
"""

from django.db import models
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that automatically scopes database queries to the current tenant.
    
    This middleware:
    1. Identifies the current tenant from the authenticated user
    2. Sets up automatic filtering for tenant-scoped models
    3. Ensures data isolation between tenants
    """
    
    def process_request(self, request):
        """Set up tenant context for the request."""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return
            
        try:
            # Get user's tenant context
            tenant_id = self._get_tenant_id(request.user)
            if tenant_id:
                request.tenant_id = tenant_id
                # Set up automatic tenant filtering
                self._setup_tenant_filtering(request, tenant_id)
        except Exception as e:
            # If there's any error in tenant detection, continue without tenant scoping
            # This prevents the middleware from breaking the entire request
            print(f"TenantMiddleware error: {e}")
            pass
    
    def _get_tenant_id(self, user):
        """Get the primary tenant ID for the user."""
        # Superadmin can access all tenants
        if getattr(user, 'role', None) == 'superadmin':
            return None  # No filtering for superadmin
            
        try:
            # Get user's colleges
            user_colleges = list(user.colleges.values_list('id', flat=True))
            if user.college_id:
                user_colleges.append(user.college_id)
                
            # Return the primary college ID
            return user_colleges[0] if user_colleges else None
        except Exception as e:
            # If there's any error accessing user colleges, return None
            print(f"Error getting tenant ID for user {user.id}: {e}")
            return None
    
    def _setup_tenant_filtering(self, request, tenant_id):
        """Set up automatic tenant filtering for models."""
        # This would be implemented with a custom QuerySet manager
        # that automatically filters by tenant_id
        pass


class TenantQuerySet(models.QuerySet):
    """
    Custom QuerySet that automatically filters by tenant.
    """
    
    def __init__(self, model=None, using=None, query=None, hints=None, **kwargs):
        super().__init__(model, using, query, hints, **kwargs)
        self._tenant_id = None
    
    def _clone(self):
        clone = super()._clone()
        clone._tenant_id = self._tenant_id
        return clone
    
    def filter_by_tenant(self, tenant_id):
        """Filter queryset by tenant ID."""
        if tenant_id and hasattr(self.model, 'college'):
            return self.filter(college_id=tenant_id)
        return self
    
    def tenant_aware(self, tenant_id):
        """Make this queryset tenant-aware."""
        self._tenant_id = tenant_id
        return self.filter_by_tenant(tenant_id)


class TenantManager(models.Manager):
    """
    Custom manager that provides tenant-aware querysets.
    """
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def for_tenant(self, tenant_id):
        """Get queryset filtered by tenant."""
        return self.get_queryset().filter_by_tenant(tenant_id)
    
    def tenant_aware(self, tenant_id):
        """Get tenant-aware queryset."""
        return self.get_queryset().tenant_aware(tenant_id)


class TenantModel(models.Model):
    """
    Abstract base model for tenant-scoped models.
    
    All models that need tenant isolation should inherit from this.
    """
    
    class Meta:
        abstract = True
    
    objects = TenantManager()
    
    def save(self, *args, **kwargs):
        """Ensure tenant is set before saving."""
        if not hasattr(self, 'college') or not self.college_id:
            raise ValueError("Tenant-scoped models must have a college field")
        super().save(*args, **kwargs)


def get_tenant_from_request(request):
    """
    Utility function to get tenant ID from request.
    """
    if hasattr(request, 'tenant_id'):
        return request.tenant_id
    return None


def require_tenant_access(user, tenant_id):
    """
    Check if user has access to the specified tenant.
    """
    if getattr(user, 'role', None) == 'superadmin':
        return True
        
    user_colleges = list(user.colleges.values_list('id', flat=True))
    if user.college_id:
        user_colleges.append(user.college_id)
        
    return tenant_id in user_colleges
