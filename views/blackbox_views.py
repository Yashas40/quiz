"""
Django view snippets showing integration with utils.blackbox_validator.validate_payload

This file contains example endpoints demonstrating consistent Blackbox-style
error JSON when payload validation fails.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from utils.blackbox_validator import validate_payload


@csrf_exempt
def generate_or_edit_package(request):
    """Accepts POST with either GENERATE payload or EDIT payload and validates it.

    Returns JSON: { status: 'ok' | 'error', error_message: null | string }
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "error_message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": "error", "error_message": "Invalid JSON"}, status=400)

    valid, err = validate_payload(data)
    if not valid:
        return JsonResponse({"status": "error", "error_message": err}, status=400)

    # If valid, proceed to generation/edit logic (omitted here)
    return JsonResponse({"status": "ok", "error_message": None})
