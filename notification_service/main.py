import os
import asyncio
from aio_pika import connect
from app.consumer import on_message

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

async def main():
    # Wait for RabbitMQ to start (simplified wait strategy)
    await asyncio.sleep(10) 
    
    print(" [Notification] Connecting to RabbitMQ...")
    try:
        connection = await connect(RABBITMQ_URL)
    except Exception as e:
        print(f" [Notification] Failed to connect: {e}")
        return

    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("health_events", type="topic")
        
        # Declare queue
        queue = await channel.declare_queue("notification_queue", durable=True)
        
        # Bind queue to exchange using wildcard to catch all health record events
        # health.record.created, health.record.updated, health.record.deleted
        await queue.bind(exchange, routing_key="health.record.#")
        
        print(" [Notification] Waiting for messages...")
        await queue.consume(on_message)
        
        # Keep running
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
