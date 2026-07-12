"""Request-scoped RLS context management.

For session-authenticated requests (Django admin, DRF browsable API) the user
is known when this middleware runs, so we set the context up front. For JWT
requests the user isn't resolved until DRF runs its authenticator, so the RLS
auth classes (see ``authentication.py``) set the context at that point. Either
way, we always reset in ``finally`` so no context leaks across requests.
"""
from .context import apply_user_context, clear_context


class RLSContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            apply_user_context(user)
        else:
            # Fail closed: RLS tables return zero rows until an authenticator
            # establishes a real user context.
            clear_context()
        try:
            return self.get_response(request)
        finally:
            clear_context()
