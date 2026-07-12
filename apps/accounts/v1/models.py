from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    MANAGER = "MANAGER", "Manager"
    GOVERNANCE_OFFICER = "GOVERNANCE_OFFICER", "Governance Officer"
    EMPLOYEE = "EMPLOYEE", "Employee"


class UserManager(DjangoUserManager):
    """Email-aware manager; keeps username support for admin compatibility."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom user so we can attach ESG roles and JWT claims from day one.

    Introduced before the first migration deliberately — swapping the user
    model later in a Django project is painful.
    """

    email = models.EmailField("email address", unique=True)
    role = models.CharField(
        max_length=32, choices=UserRole.choices, default=UserRole.EMPLOYEE, db_index=True
    )
    department = models.ForeignKey(
        "environmental_v1.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    phone = models.CharField(max_length=20, blank=True)

    objects = UserManager()

    class Meta:
        ordering = ("username",)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_manager(self):
        return self.role in {UserRole.ADMIN, UserRole.MANAGER}
