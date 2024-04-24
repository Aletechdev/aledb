# mysite/asgi.py
import os

from channels.auth import AuthMiddlewareStack

from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from goggles.consumers import GogglesConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'https': get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/goggles/', GogglesConsumer.as_asgi()),
        ])
    ),
})
