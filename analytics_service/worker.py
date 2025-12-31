import os
import asyncio
from aio_pika import connect
from app.database import create_db_and_tables
from app.consumer import on_message

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

async def main():
    # Ensure tables exist (worker might start before API)
    create_db_and_tables()
    
    await asyncio.sleep(10) # Wait for RMQ
    print(" [Analytics Worker] Connecting to RabbitMQ...")
    
    try:
        connection = await connect(RABBITMQ_URL)
    except Exception as e:
         print(f" [Analytics Worker] Connection failed: {e}")
         return

    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("health_events", type="topic")
        queue = await channel.declare_queue("analytics_queue", durable=True)
        
        # Bind specifically to creation events for aggregation
        await queue.bind(exchange, routing_key="health.record.created")
        
        print(" [Analytics Worker] Waiting for messages...")
        await queue.consume(on_message)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
