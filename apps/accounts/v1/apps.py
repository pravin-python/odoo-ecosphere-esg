from django.apps import AppConfig


class AccountsV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts.v1"
    label = "accounts_v1"
    verbose_name = "Accounts (v1)"
