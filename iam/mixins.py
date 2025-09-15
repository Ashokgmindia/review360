from rest_framework import permissions


class CollegeScopedQuerysetMixin:
    """
    Mixin to scope queryset to the current user's college when the user has
    the college_admin role. If the model has a "college" field, it filters
    by that field; otherwise, college admins see no data.
    Superadmins are allowed full access.
    """

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()  # noqa: B024
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)  # type: ignore[attr-defined]
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        role = getattr(user, "role", None)

        # Superadmins have full access
        if role == getattr(user.__class__.Role, "SUPERADMIN", "superadmin"):
            return qs

        # Determine allowed college ids for the user
        user_college_ids = []
        try:
            user_college_ids = list(getattr(user, "colleges").values_list("id", flat=True))  # type: ignore[attr-defined]
        except Exception:
            user_college_ids = []
        fk_college_id = getattr(user, "college_id", None)
        if fk_college_id:
            user_college_ids.append(fk_college_id)
        user_college_ids = list({cid for cid in user_college_ids if cid})
        if not user_college_ids:
            return qs.none()

        # Primary scoping: models with a direct college field
        model = qs.model
        if any(f.name == "college" for f in model._meta.get_fields()):
            qs = qs.filter(college_id__in=user_college_ids)
        else:
            # Related scoping via declared relations on the view
            tenant_relations = getattr(self, "tenant_relations", [])  # e.g., ["activity_sheet__college_id"]
            if tenant_relations:
                from django.db.models import Q
                cond = Q()
                for rel in tenant_relations:
                    cond |= Q(**{f"{rel}__in": user_college_ids})
                qs = qs.filter(cond)
            else:
                return qs.none()

        return qs


class IsAuthenticatedAndScoped(permissions.IsAuthenticated):
    """Authenticated users only; scoping is handled by the mixin's queryset."""
    pass


class RolePermission(permissions.BasePermission):
    """
    Simple role-based permission utility.
    Usage: set view.allowed_roles = {"superadmin", "college_admin", "teacher"}
    """

    def has_permission(self, request, view):
        allowed = getattr(view, "allowed_roles", None)
        if not allowed:
            return True
        return getattr(request.user, "role", None) in allowed


class ActionRolePermission(permissions.BasePermission):
    """
    Per-action role permissions. Define on the view:
    role_perms = {
        "list": {"superadmin", "college_admin", "teacher", "student"},
        "retrieve": {...},
        "create": {"superadmin", "college_admin"},
        "update": {"superadmin", "college_admin"},
        "partial_update": {"superadmin", "college_admin"},
        "destroy": {"superadmin", "college_admin"},
    }
    If not provided, defaults to allowing all authenticated roles.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        mapping = getattr(view, "role_perms", None)
        if not mapping:
            return True
        action = getattr(view, "action", None)
        allowed = mapping.get(action)
        if allowed is None:
            # Fallback to safe default: allow read-only to all roles, restrict writes
            if action in {"list", "retrieve"}:
                return True
            allowed = {"superadmin", "college_admin"}
        return getattr(request.user, "role", None) in allowed


