from channels import route
from delivery_system import asysn_tasks


channel_routing = [
    route('websocket.connect', asysn_tasks.ws_connect),
    route('websocket.receive', asysn_tasks.ws_receive),
    route('websocket.disconnect', asysn_tasks.ws_disconnect),
]