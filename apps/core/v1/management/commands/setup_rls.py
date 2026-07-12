"""Apply (or preview/remove) the Postgres row-level-security policies.

    python manage.py setup_rls              # apply RLS to all registered tables
    python manage.py setup_rls --dry-run    # print the SQL, touch nothing
    python manage.py setup_rls --drop       # remove all RLS policies

Run after every ``migrate``. Policies are derived from the declarative registry
in ``apps/core/v1/rls/registry.py``.
"""
from django.core.management.base import BaseCommand
from django.db import connection

from apps.core.v1.rls import sql


class Command(BaseCommand):
    help = "Enable/disable Postgres row-level security for EcoSphere tables."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Print the SQL without executing it.")
        parser.add_argument("--drop", action="store_true",
                            help="Remove RLS policies instead of applying them.")

    def handle(self, *args, **options):
        script = sql.build_disable_sql() if options["drop"] else sql.build_enable_sql()

        if options["dry_run"]:
            self.stdout.write(script)
            return

        if connection.vendor != "postgresql":
            self.stderr.write(self.style.ERROR(
                f"RLS requires PostgreSQL, but the default connection is "
                f"'{connection.vendor}'. Configure DATABASE_URL and retry."
            ))
            return

        with connection.cursor() as cur:
            cur.execute(script)

        action = "removed" if options["drop"] else "applied"
        self.stdout.write(self.style.SUCCESS(
            f"RLS policies {action} for {len(sql.reg.RLS_RULES)} tables."
        ))
