"""Periodic ESG maintenance — safe to run daily (e.g. via cron/scheduler).

Steps:
  1. Recompute every department's ESG scores + the overall score.
  2. Flag overdue compliance issues and notify their owners.
  3. Enrol users into pending policy acknowledgements and remind those still open.

Usage:
    python manage.py run_esg_maintenance
    python manage.py run_esg_maintenance --skip-reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Recompute ESG scores, flag overdue compliance issues, send policy reminders."

    def add_arguments(self, parser):
        parser.add_argument("--skip-reminders", action="store_true",
                            help="Do not send policy acknowledgement reminders.")
        parser.add_argument("--year", type=int, default=None,
                            help="Reporting year to score (defaults to configured year).")

    def handle(self, *args, **options):
        from apps.core.v1.rls.context import rls_admin

        # Cross-department maintenance with no request user: bypass RLS for the
        # whole run so scoring/notification queries see every row.
        with rls_admin():
            self._run(options)

    def _run(self, options):
        from apps.compliance.v1.models import (
            ComplianceIssue,
            ESGPolicy,
            PolicyAcknowledgement,
        )
        from apps.environmental.v1.scoring import overall_esg_score, recompute_all
        from apps.notifications.v1.models import Notification, notify

        year = options["year"]

        # 1. Scores
        rows = recompute_all(period_year=year)
        overall = overall_esg_score(period_year=year)
        self.stdout.write(self.style.SUCCESS(
            f"Recomputed {len(rows)} department score(s). Overall ESG Score: {overall}"
        ))

        # 2. Overdue compliance issues
        today = timezone.now().date()
        overdue = (
            ComplianceIssue.objects.exclude(status=ComplianceIssue.Status.RESOLVED)
            .filter(due_date__lt=today)
        )
        for issue in overdue.select_related("owner"):
            notify(
                issue.owner,
                title=f"OVERDUE compliance issue: {issue.title}",
                message=f"Was due {issue.due_date}. Please resolve or reassign.",
                category=Notification.Category.COMPLIANCE,
            )
        self.stdout.write(self.style.WARNING(f"Flagged {overdue.count()} overdue issue(s)."))

        # 3. Policy acknowledgement enrolment + reminders
        if options["skip_reminders"]:
            return

        from django.contrib.auth import get_user_model

        User = get_user_model()
        users = User.objects.filter(is_active=True)
        policies = ESGPolicy.objects.filter(is_active=True)

        created = 0
        for policy in policies:
            for user in users:
                _, was_created = PolicyAcknowledgement.objects.get_or_create(
                    policy=policy, employee=user
                )
                created += int(was_created)

        pending = PolicyAcknowledgement.objects.filter(acknowledged_at__isnull=True)
        for ack in pending.select_related("employee", "policy"):
            notify(
                ack.employee,
                title=f"Action needed: acknowledge '{ack.policy.title}'",
                message="Please review and acknowledge this ESG policy.",
                category=Notification.Category.COMPLIANCE,
            )
        self.stdout.write(self.style.SUCCESS(
            f"Enrolled {created} new acknowledgement(s); reminded {pending.count()} pending."
        ))
