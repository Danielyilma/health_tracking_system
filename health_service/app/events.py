import os
import json
from aio_pika import connect, Message, DeliveryMode

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

async def publish_event(event_type: str, data: dict):
    connection = await connect(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        
        # Publish to 'health_events' exchange
        # We declare it as a 'topic' exchange so consumers can subscribe to patterns
        exchange = await channel.declare_exchange("health_events", type="topic")
        
        message_body = json.dumps(data).encode()
        message = Message(
            message_body,
            delivery_mode=DeliveryMode.PERSISTENT
        )
        
        routing_key = f"health.record.{event_type}"
        await exchange.publish(message, routing_key=routing_key)
        print(f" [x] Sent {routing_key}:{data}")
