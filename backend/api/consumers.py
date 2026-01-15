# backend/api/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StockConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. Get the stock symbol from the URL (e.g., ws/stock/AAPL/)
        self.symbol = self.scope['url_route']['kwargs']['symbol'].upper()
        self.group_name = f"stock_{self.symbol}"

        # 2. Join the Redis Channel Group for this symbol
        # This allows Celery to push updates to this group later
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # 3. Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group when user disconnects
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # This method is called when Redis sends a message to the group
    async def stock_update(self, event):
        price = event['price']

        # Send the data down to the React Frontend
        await self.send(text_data=json.dumps({
            'symbol': self.symbol,
            'price': price
        }))