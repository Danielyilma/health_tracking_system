import json
from aio_pika import IncomingMessage
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalyticsStats

async def process_creation_event(event: dict):
    username = event.get('username')
    steps = event.get('steps', 0)
    
    with Session(engine) as session:
        statement = select(AnalyticsStats).where(AnalyticsStats.username == username)
        stats = session.exec(statement).first()
        
        if not stats:
            stats = AnalyticsStats(username=username, total_steps=0, record_count=0)
        
        stats.total_steps += steps
        stats.record_count += 1
        if stats.record_count > 0:
            stats.average_steps = stats.total_steps / stats.record_count
        
        session.add(stats)
        session.commit()
        print(f" [Analytics] Updated stats for {username}: Avg Steps {stats.average_steps:.2f}")

async def on_message(message: IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        routing_key = message.routing_key
        
        print(f" [Analytics] Received event: {routing_key}")
        
        # We only aggregate on creation to ensure data consistency in this simple model.
        # Handling updates/deletes in an aggregation-only view requires more complex logic (CQRS/Event Sourcing)
        if "created" in routing_key:
            await process_creation_event(event)
        else:
            print(f" [Analytics] Skipping non-creation event for aggregation.")
