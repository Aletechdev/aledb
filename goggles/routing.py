from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from .consumers import GogglesConsumer

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/goggles/', GogglesConsumer.as_asgi()),
    ])
})
