"""Notify owners of overdue compliance issues.

Run on a schedule (cron / Celery beat) instead of checking inside a request
middleware — a nightly sweep is cheaper and keeps request latency flat:

    python manage.py flag_overdue_issues
"""
from django.core.management.base import BaseCommand

from apps.compliance.v1.models import ComplianceIssue
from apps.core.v1.rls.context import rls_admin
from apps.notifications.v1.models import Notification, notify


class Command(BaseCommand):
    help = "Send a notification to the owner of every overdue compliance issue."

    def handle(self, *args, **options):
        # Org-wide sweep with no request user -> bypass RLS.
        with rls_admin():
            count = self._notify_owners()
        self.stdout.write(self.style.SUCCESS(f"Notified {count} owner(s) of overdue issues."))

    def _notify_owners(self):
        overdue = ComplianceIssue.objects.overdue().select_related("owner")
        count = 0
        for issue in overdue:
            notify(
                issue.owner,
                title=f"Overdue: {issue.title}",
                message=f"Issue was due {issue.due_date}. Severity: {issue.severity}.",
                category=Notification.Category.COMPLIANCE,
            )
            count += 1
        return count
