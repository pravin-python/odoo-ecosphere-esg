"""RLS-aware DRF authenticators.

They behave exactly like the stock classes but, on a successful auth, push the
resolved user's identity into the Postgres RLS session context so every query
in the view is row-filtered by the database.
"""
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .rls.context import apply_user_context


class RLSJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            apply_user_context(user)
        return result


class RLSSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _ = result
            apply_user_context(user)
        return result
