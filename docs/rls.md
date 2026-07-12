# Row-Level Security (RLS) + RBAC

EcoSphere enforces visibility at the **database** level using PostgreSQL
row-level security, not just in the Django ORM. Even a raw SQL client connecting
as the app role only sees rows the current user's role allows. This is defense
in depth: a missing `.filter()` in a view can't leak another department's data.

## How it works

1. **The app connects as a restricted role.** `ecosphere_app` is
   `NOSUPERUSER NOBYPASSRLS` and owns the tables, which are marked
   `FORCE ROW LEVEL SECURITY` — so policies apply even to the table owner.
   (See [`scripts/db/init.sql`](../scripts/db/init.sql).)

2. **Each request sets Postgres session variables** identifying the user:
   `app.user_id`, `app.role`, `app.department_id`.
   - Session-authenticated requests (admin, browsable API): set by
     [`RLSContextMiddleware`](../apps/core/v1/rls/middleware.py).
   - JWT requests: set by [`RLSJWTAuthentication`](../apps/core/v1/authentication.py)
     the moment the token is validated (before the view queries anything).
   - The middleware **always resets** the variables in a `finally` block, so a
     pooled connection can't leak context between requests.

3. **Policies read those variables** via helper functions in the `app` schema
   (`app.current_user_id()`, `app.current_role()`, `app.current_dept()`,
   `app.is_bypass()`). If no context is set, every RLS table returns **zero
   rows** — the system fails closed.

4. **Policies are generated from a declarative registry**
   ([`apps/core/v1/rls/registry.py`](../apps/core/v1/rls/registry.py)) so table
   names are never hard-coded. Apply them with `manage.py setup_rls`.

## RBAC visibility matrix (default)

| Data | ADMIN | GOVERNANCE_OFFICER | MANAGER | EMPLOYEE |
|---|---|---|---|---|
| Department (org unit) | all | all | own dept | own dept |
| Operational: carbon, fleet, procurement, manufacturing, audits | all | all | own dept | own dept |
| Compliance issues | all | all | own dept | own dept + owned |
| Personal: notifications, gamification profile | all | all | own only | own only |
| CSR participations, policy acknowledgements | all | all | own dept members | own only |

`ADMIN` and `GOVERNANCE_OFFICER` are "privileged" (org-wide) because both need
oversight for ESG scoring and reporting. To change any rule, edit the registry
and re-run `setup_rls`.

> **Note:** the `accounts_v1_user` table has **no** RLS on purpose — authentication
> must load the user row *before* any context exists (avoiding a bootstrap
> deadlock). Restrict user listing at the API layer instead.

## Server-side jobs

Management commands / scheduled jobs have no request user. Wrap cross-department
work in the bypass context manager:

```python
from apps.core.v1.rls.context import rls_admin

with rls_admin():
    recompute_all_department_scores()
```

`run_esg_maintenance` and `flag_overdue_issues` already do this.

## Setup & verification

```bash
# 1. Start Postgres (creates the restricted ecosphere_app role)
docker compose up -d db

# 2. Schema + policies
python manage.py migrate
python manage.py setup_rls            # --dry-run to preview, --drop to remove

# 3. Prove it
python manage.py shell < scripts/verify_rls.py
```

`verify_rls.py` creates two departments and asserts each role sees only the rows
RLS permits (managers scoped to their dept, employees to their own personal
rows, admin sees all, no-context sees nothing).

## Production hardening

The `app.bypass_rls` GUC is a convenience for trusted server jobs. For stronger
isolation in production, run maintenance under a **separate** `BYPASSRLS` role
(a second `DATABASES` alias) instead of the GUC, so application code paths can
never elevate themselves.
