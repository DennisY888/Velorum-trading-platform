# backend/backend/asgi.py

import os
import django

# 1. Initialize Django settings first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.routing import websocket_urlpatterns

# 2. Define the Routing Logic
application = ProtocolTypeRouter({
    # If the request is HTTP, give it to standard Django
    "http": get_asgi_application(),

    # If the request is WebSocket, pass it through Auth middleware, then to our URL router
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})