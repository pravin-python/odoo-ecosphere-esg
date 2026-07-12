import uuid

from django.conf import settings
from django.db import models

from .managers import ActiveManager, SoftDeleteManager


class TimeStampedModel(models.Model):
    """Abstract base adding self-managed created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base exposing a non-guessable public identifier.

    The integer PK stays internal; ``public_id`` is what we expose over the
    API so record counts and ordering can't be inferred from URLs.
    """

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Sensible default base: public id + timestamps + soft delete."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()
    active = ActiveManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])


class ActivityLog(TimeStampedModel):
    """Immutable security/governance audit trail of user actions.

    Written by ``ActivityLogMiddleware`` for every mutating API request so
    governance officers can answer "who changed what, when, from where".
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["actor", "created_at"])]

    def __str__(self):
        actor = self.actor or "anonymous"
        return f"{actor} {self.method} {self.path} -> {self.status_code}"
