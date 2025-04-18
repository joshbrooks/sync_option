from datetime import datetime
from uuid import UUID
from django.utils.http import http_date, parse_http_date_safe
from django.http import HttpResponseNotModified

def uuid7_to_datetime(uuid_str: str) -> datetime:
    """Extract timestamp from UUIDv7 string"""
    try:
        # Convert string to UUID
        uuid = UUID(uuid_str)
        # Extract timestamp (first 48 bits)
        timestamp_ms = (uuid.int >> 80) & ((1 << 48) - 1)
        # Convert to datetime (UUIDv7 uses Unix timestamp in milliseconds)
        return datetime.fromtimestamp(timestamp_ms / 1000)
    except (ValueError, TypeError):
        return datetime.now()

REQUEST_PATH_PREFIX = '/api/sync-option/'

class PreventCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(REQUEST_PATH_PREFIX):
            request._should_update_cache = False
        return self.get_response(request)

class SyncOptionCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process GET/HEAD requests to API endpoints
        if not request.path.startswith(REQUEST_PATH_PREFIX):
            return self.get_response(request)

        response = self.get_response(request)
        
        # Add cache headers for stale-while-revalidate strategy
        # Max-age 0 means Django will not cache the response
        response["Cache-Control"] = "public, max-age=0, stale-while-revalidate=86400"
        response["X-Is-Cacheable"] = "true"
        return response 