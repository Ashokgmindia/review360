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
        user = getattr(self, "request", None).user  # type: ignore[attr-defined]
        role = getattr(user, "role", None)
        if role == getattr(user.__class__.Role, "SUPERADMIN", "superadmin"):
            return qs
        if role == getattr(user.__class__.Role, "COLLEGE_ADMIN", "college_admin"):
            # If model has a college field, filter; else return none
            model = qs.model
            if any(f.name == "college" for f in model._meta.get_fields()):
                # Support multi-college users; fallback to single FK
                user_college_ids = []
                try:
                    user_college_ids = list(getattr(user, "colleges").values_list("id", flat=True))  # type: ignore[attr-defined]
                except Exception:
                    user_college_ids = []
                fk_college_id = getattr(user, "college_id", None)
                if fk_college_id:
                    user_college_ids.append(fk_college_id)
                user_college_ids = list({cid for cid in user_college_ids if cid})
                if user_college_ids:
                    return qs.filter(college_id__in=user_college_ids)
            return qs.none()
        return qs.none()


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


