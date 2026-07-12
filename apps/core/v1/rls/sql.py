"""Generate Postgres RLS SQL from the declarative registry.

Kept separate from the management command so the SQL can be unit-tested and
printed (``setup_rls --dry-run``) without a live database.
"""
from django.apps import apps

from . import registry as reg

POLICY_NAME = "rls_default"
ACCOUNTS_USER_TABLE = "accounts_v1_user"

# Helper functions live in a dedicated `app` schema. They read the per-request
# GUC variables set by RLSContextMiddleware / the RLS auth classes.
HELPER_FUNCTIONS_SQL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE OR REPLACE FUNCTION app.current_user_id() RETURNS integer
    LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.user_id', true), '')::integer $$;

CREATE OR REPLACE FUNCTION app.current_role() RETURNS text
    LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.role', true), '') $$;

CREATE OR REPLACE FUNCTION app.current_dept() RETURNS integer
    LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.department_id', true), '')::integer $$;

CREATE OR REPLACE FUNCTION app.is_bypass() RETURNS boolean
    LANGUAGE sql STABLE AS $$ SELECT COALESCE(current_setting('app.bypass_rls', true) = 'on', false) $$;
"""


def _table(model_label: str) -> str:
    return apps.get_model(model_label)._meta.db_table


def _privileged_clause(roles) -> str:
    quoted = ", ".join(f"'{r}'" for r in roles)
    return f"app.current_role() IN ({quoted})"


def _scope_predicate(rule) -> str:
    """Return the boolean SQL expression that grants row visibility for a rule."""
    if rule.scope == reg.SELF_DEPARTMENT:
        return "id = app.current_dept()"

    if rule.scope == reg.DEPARTMENT:
        return f"{rule.column} = app.current_dept()"

    if rule.scope == reg.OWNER:
        return f"{rule.column} = app.current_user_id()"

    if rule.scope == reg.DEPARTMENT_VIA:
        ref = _table(rule.ref_model)
        return (
            f"EXISTS (SELECT 1 FROM {ref} _r "
            f"WHERE _r.id = {rule.column} AND _r.{rule.ref_column} = app.current_dept())"
        )

    if rule.scope == reg.OWNER_OR_DEPARTMENT_VIA:
        ref = _table(rule.ref_model)
        return (
            f"{rule.column} = app.current_user_id() "
            f"OR EXISTS (SELECT 1 FROM {ref} _r "
            f"WHERE _r.id = {rule.ref_column} AND _r.department_id = app.current_dept())"
        )

    if rule.scope == reg.OWNER_OR_DEPT_MANAGER:
        # Owner sees their own row; a MANAGER sees rows owned by users in their dept.
        return (
            f"{rule.column} = app.current_user_id() "
            f"OR (app.current_role() = 'MANAGER' AND EXISTS ("
            f"SELECT 1 FROM {ACCOUNTS_USER_TABLE} _u "
            f"WHERE _u.id = {rule.column} AND _u.department_id = app.current_dept()))"
        )

    raise ValueError(f"Unknown scope: {rule.scope}")


def build_policy_predicate(rule) -> str:
    """Full predicate: bypass OR privileged-role OR scope-specific visibility."""
    return (
        f"app.is_bypass() OR {_privileged_clause(rule.privileged_roles)} "
        f"OR ({_scope_predicate(rule)})"
    )


def build_table_sql(rule) -> str:
    table = _table(rule.model)
    predicate = build_policy_predicate(rule)
    return (
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\n"
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;\n"
        f"DROP POLICY IF EXISTS {POLICY_NAME} ON {table};\n"
        f"CREATE POLICY {POLICY_NAME} ON {table}\n"
        f"    FOR ALL\n"
        f"    USING ({predicate})\n"
        f"    WITH CHECK ({predicate});\n"
    )


def build_enable_sql() -> str:
    parts = [HELPER_FUNCTIONS_SQL.strip(), ""]
    for rule in reg.RLS_RULES:
        parts.append(f"-- {rule.model}  [{rule.scope}]")
        parts.append(build_table_sql(rule))
    return "\n".join(parts)


def build_disable_sql() -> str:
    lines = []
    for rule in reg.RLS_RULES:
        table = _table(rule.model)
        lines.append(f"DROP POLICY IF EXISTS {POLICY_NAME} ON {table};")
        lines.append(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        lines.append(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    return "\n".join(lines) + "\n"
