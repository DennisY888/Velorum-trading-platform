# backend/api/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Maps ws://.../ws/stock/AAPL/ to the StockConsumer
    re_path(r'ws/stock/(?P<symbol>\w+)/$', consumers.StockConsumer.as_asgi()),
]