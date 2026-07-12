from rest_framework.permissions import SAFE_METHODS, BasePermission


class RolePermission(BasePermission):
    """Base class for role-gated endpoints.

    Subclass and set ``allowed_roles``. Safe (read-only) methods are always
    permitted for authenticated users; writes require a matching role.
    """

    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if user.is_superuser:
            return True
        return getattr(user, "role", None) in self.allowed_roles


class IsAdmin(RolePermission):
    allowed_roles = ("ADMIN",)


class IsManager(RolePermission):
    allowed_roles = ("ADMIN", "MANAGER")


class IsGovernanceOfficer(RolePermission):
    allowed_roles = ("ADMIN", "GOVERNANCE_OFFICER")


class CanManage(RolePermission):
    """Create/manage records: staff roles only; everyone else is read-only."""

    allowed_roles = ("ADMIN", "MANAGER", "GOVERNANCE_OFFICER")


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: only the owning user may modify; others read-only."""

    owner_field = "owner"

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, getattr(view, "owner_field", self.owner_field), None)
        return owner == request.user or request.user.is_superuser
