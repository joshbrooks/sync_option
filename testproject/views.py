from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health_check(request):
    """
    Basic health check endpoint that verifies:
    1. The application is running
    2. Database connections are working
    """
    # Check database connections
    db_healthy = True
    try:
        for name in connections:
            cursor = connections[name].cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
    except OperationalError:
        db_healthy = False

    status = 200 if db_healthy else 503
    health_status = {
        'status': 'healthy' if db_healthy else 'unhealthy',
        'database': 'up' if db_healthy else 'down',
    }

    return JsonResponse(health_status, status=status) 