import logging

logger = logging.getLogger("ecosphere.activity")

# Only these methods mutate state and are worth persisting to the audit trail.
_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ActivityLogMiddleware:
    """Persist an immutable audit record for every mutating API request.

    This is the security/governance backbone: it answers "who did what,
    when, and from where" without each view having to remember to log.
    Read requests are skipped to keep the trail meaningful and cheap.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method in _AUDITED_METHODS and request.path.startswith("/api/"):
            self._record(request, response)
        return response

    def _record(self, request, response):
        # Imported lazily so the app registry is fully populated first.
        from apps.core.v1.models import ActivityLog

        user = getattr(request, "user", None)
        actor = user if getattr(user, "is_authenticated", False) else None
        try:
            ActivityLog.objects.create(
                actor=actor,
                method=request.method,
                path=request.path[:255],
                status_code=response.status_code,
                ip_address=_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
            )
        except Exception:  # pragma: no cover - auditing must never break a request
            logger.exception("Failed to write activity log")
