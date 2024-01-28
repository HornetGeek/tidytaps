from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/order/(?P<order_id>[a-f\d-]+)/?$", consumers.OrderConsumer.as_asgi()),
]