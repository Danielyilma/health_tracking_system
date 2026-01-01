import os
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from aio_pika import connect
from app.database import create_db_and_tables
from app.api import router as notification_router
from app.consumer import on_message

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create DB and Connect to RabbitMQ
    create_db_and_tables()
    
    # Run consumer in background task
    connection = None
    try:
        connection = await connect(RABBITMQ_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("health_events", type="topic")
        queue = await channel.declare_queue("notification_queue", durable=True)
        
        # Bind to health records and insights
        await queue.bind(exchange, routing_key="health.record.#")
        await queue.bind(exchange, routing_key="analysis.insight.#")
        
        print(" [Notification] Waiting for messages...")
        await queue.consume(on_message)
        
        # yield control back to FastAPI
        yield
        
    except Exception as e:
        print(f" [Notification] Startup failed: {e}")
        yield

    # Shutdown
    if connection:
        await connection.close()

app = FastAPI(title="Notification Service", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for direct access setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notification_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
