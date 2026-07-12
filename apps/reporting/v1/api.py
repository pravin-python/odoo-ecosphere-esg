"""Report export endpoint — streams CSV / XLSX / PDF for the module Export button."""
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from . import exporters, services

_TYPES = {"ENVIRONMENTAL", "SOCIAL", "GOVERNANCE", "ESG_SUMMARY"}
_FORMATS = {"csv", "xlsx", "pdf"}


class ReportExportView(APIView):
    """GET /api/v1/reports/export/?type=ESG_SUMMARY&format=pdf

    Builds the requested report (RLS-scoped data) and returns it as a file
    download. Reused by every module's Export button.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        report_type = (request.query_params.get("type") or "ESG_SUMMARY").upper()
        # NB: use "fmt", not "format" — DRF reserves ?format= for content
        # negotiation and would 404 before this view runs.
        fmt = (request.query_params.get("fmt") or "pdf").lower()
        if report_type not in _TYPES:
            raise ValidationError({"type": f"Unknown report type. Use one of {sorted(_TYPES)}."})
        if fmt not in _FORMATS:
            raise ValidationError({"format": f"Unknown format. Use one of {sorted(_FORMATS)}."})

        filters = {
            "department": request.query_params.get("department"),
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
        }
        result = services.build_report(report_type, {k: v for k, v in filters.items() if v})
        payload, content_type, filename = exporters.export_report(result, fmt)

        response = HttpResponse(payload, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
