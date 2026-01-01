import json
from datetime import datetime
from aio_pika import IncomingMessage
from sqlmodel import Session, select
from app.database import engine
from app.models import AnalyticsStats, DailyHealthStats, HealthInsight
from app.engine import generate_insights

async def process_creation_event(event: dict):
    username = event.get('username')
    steps = event.get('steps') or 0
    sleep = event.get('sleep_hours') or 0.0
    weight = event.get('weight') or 0.0
    heart_rate = event.get('heart_rate')
    
    timestamp_str = event.get('timestamp')
    try:
        dt = datetime.fromisoformat(timestamp_str)
        date_obj = dt.date()
    except (ValueError, TypeError):
        date_obj = datetime.utcnow().date()
        
    with Session(engine) as session:
        # 1. Update Global Stats (Legacy)
        statement = select(AnalyticsStats).where(AnalyticsStats.username == username)
        stats = session.exec(statement).first()
        if not stats:
            stats = AnalyticsStats(username=username, total_steps=0, record_count=0)
        stats.total_steps += steps
        stats.record_count += 1
        if stats.record_count > 0:
            stats.average_steps = stats.total_steps / stats.record_count
        session.add(stats)
        
        # 2. Update Daily Stats
        stmt = select(DailyHealthStats).where(
            DailyHealthStats.username == username,
            DailyHealthStats.date == date_obj
        )
        daily = session.exec(stmt).first()
        if not daily:
            daily = DailyHealthStats(username=username, date=date_obj)
            
        daily.total_steps += steps
        daily.sleep_hours += sleep
        if weight > 0:
            daily.avg_weight = weight # Simplified: just take latest or we can avg
            
        if heart_rate:
            if daily.heart_rate_count == 0:
                daily.avg_heart_rate = float(heart_rate)
                daily.min_heart_rate = heart_rate
                daily.max_heart_rate = heart_rate
            else:
                # Iterative average
                total_hr = daily.avg_heart_rate * daily.heart_rate_count + heart_rate
                daily.avg_heart_rate = total_hr / (daily.heart_rate_count + 1)
                
                daily.min_heart_rate = min(daily.min_heart_rate, heart_rate)
                daily.max_heart_rate = max(daily.max_heart_rate, heart_rate)
            daily.heart_rate_count += 1
            
        session.add(daily)
        session.commit()
        session.refresh(daily)
        
        # 3. Generate Insights
        insights = generate_insights(username, daily, session)
        for insight in insights:
            session.add(insight)
        
        session.commit()
        print(f" [Analytics] Processed event for {username}. Generated {len(insights)} insights.")

async def on_message(message: IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        routing_key = message.routing_key
        
        print(f" [Analytics] Received event: {routing_key}")
        
        if "created" in routing_key:
            await process_creation_event(event)
        else:
             print(f" [Analytics] Skipping non-creation event for aggregation.")
