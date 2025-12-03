# vitanips/core/health_views.py
from django.http import JsonResponse
from django.db import connection
from django.conf import settings

def health_check(request):
    """
    Simple health check endpoint for fly.io and other monitoring tools.
    Returns 200 if the application is healthy, 503 otherwise.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'debug': settings.DEBUG,
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
        }, status=503)

