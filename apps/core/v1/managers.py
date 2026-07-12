from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        from django.utils import timezone

        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class ActiveManager(models.Manager):
    """Manager returning rows flagged ``is_active=True`` (and not deleted)."""

    def get_queryset(self):
        qs = SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
        if any(f.name == "is_active" for f in self.model._meta.fields):
            qs = qs.filter(is_active=True)
        return qs
