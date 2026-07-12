"""Per-connection RLS session context.

Postgres RLS policies read the current user's identity from session GUC
variables (``app.user_id``, ``app.role``, ``app.department_id``). These helpers
set/clear those variables on the active Django connection.

Bootstrapping note: the ``accounts_v1_user`` table intentionally has NO RLS,
so authentication can load the user row *before* any context exists.
"""
from contextlib import contextmanager

from django.db import connection


def _pg(conn):
    return conn.vendor == "postgresql"


def _set(cursor, key, value):
    # set_config(key, value, is_local=false) -> lasts for the DB session until
    # reset. The middleware always resets in a finally block, so a pooled
    # connection can't leak one user's context into the next request.
    cursor.execute("SELECT set_config(%s, %s, false)", [key, "" if value is None else str(value)])


def apply_user_context(user, *, conn=None):
    """Load an authenticated user's identity into the connection's RLS vars."""
    conn = conn or connection
    if not _pg(conn):
        return
    with conn.cursor() as cur:
        is_super = bool(getattr(user, "is_superuser", False))
        _set(cur, "app.bypass_rls", "on" if is_super else "off")
        _set(cur, "app.user_id", user.pk if getattr(user, "is_authenticated", False) else "")
        _set(cur, "app.role", getattr(user, "role", "") or "")
        _set(cur, "app.department_id", getattr(user, "department_id", None) or "")


def clear_context(*, conn=None):
    """Reset to the anonymous/deny state (RLS tables return zero rows)."""
    conn = conn or connection
    if not _pg(conn):
        return
    with conn.cursor() as cur:
        _set(cur, "app.user_id", "")
        _set(cur, "app.role", "")
        _set(cur, "app.department_id", "")
        _set(cur, "app.bypass_rls", "off")


@contextmanager
def rls_admin(*, conn=None):
    """Temporarily bypass RLS for trusted server-side work.

    Use in management commands / scheduled jobs / data loaders that legitimately
    operate across all departments and have no request user. Example::

        with rls_admin():
            recompute_all_department_scores()
    """
    conn = conn or connection
    if not _pg(conn):
        yield
        return
    with conn.cursor() as cur:
        _set(cur, "app.bypass_rls", "on")
    try:
        yield
    finally:
        with conn.cursor() as cur:
            _set(cur, "app.bypass_rls", "off")
