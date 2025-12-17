"""
ASGI config for vitanips project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitanips.settings')
django.setup()

from django.core.asgi import get_asgi_application

# Import channels components with error handling
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from channels.security.websocket import AllowedHostsOriginValidator
    from notifications.routing import websocket_urlpatterns
    
    # Use ASGI with WebSocket support
    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                )
            )
        ),
    })
except ImportError as e:
    # Fallback to basic ASGI if channels components are not available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Channels components not available: {e}. Using basic ASGI application.")
    application = get_asgi_application()
except Exception as e:
    # Log any other errors but still provide a basic ASGI app
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error setting up ASGI application: {e}", exc_info=True)
    application = get_asgi_application()
