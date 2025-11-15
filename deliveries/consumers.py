from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

class DeliveryConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.group_type = self.scope.get('url_route', {}).get('kwargs', {}).get('group_type')
        quote_id = self.scope.get('url_route', {}).get('kwargs', {}).get('quote_id')
        delivery_id = self.scope.get('url_route', {}).get('kwargs', {}).get('delivery_id')

        if self.group_type == 'quote' and quote_id:
            self.group_name = f"quote_{quote_id}"
        elif self.group_type == 'delivery' and delivery_id:
            self.group_name = f"delivery_{delivery_id}"
        elif self.group_type == 'new_quotes':
            self.group_name = "new_quotes"
        else:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        pass

    def broadcast(self, event):
        data = event.get('data', {})
        self.send_json(data)