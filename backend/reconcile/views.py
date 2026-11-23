
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import get_disagreements


@api_view(["GET"])
def disagreements_view(request):
    org_id = request.query_params.get("org", "").strip()

    if not org_id:
        return Response(
            {"error": "org query parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    disagreements = get_disagreements(org_id)

    # Filter disagreements by reason
    reason = request.query_params.get("reason", "").strip()

    if reason:
        disagreements = [
            item
            for item in disagreements
            if item["reason"] == reason
        ]

    # Sort disagreements
    sort_field = request.query_params.get("sort", "").strip()

    allowed_sort_fields = {
        "record_id",
        "location_id",
        "reason",
        "system_a_value",
        "system_b_value",
        "value",
    }

    if sort_field:
        descending = sort_field.startswith("-")
        field = sort_field[1:] if descending else sort_field

        if field not in allowed_sort_fields:
            return Response(
                {"error": "Invalid sort field"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Alias used by the assessment API
        if field == "value":
            field = "system_a_value"

        # Keep missing values at the end for either direction
        
        # Sort non-null values while keeping NULL values last
        non_null = [
            item for item in disagreements
            if item[field] is not None
        ]

        null_values = [
            item for item in disagreements
            if item[field] is None
        ]

        non_null.sort(
            key=lambda item: item[field],
            reverse=descending,
        )

        disagreements = non_null + null_values


    return Response({
        "org": org_id,
        "count": len(disagreements),
        "results": disagreements,
    })
