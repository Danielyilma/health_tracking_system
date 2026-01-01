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
            # Publish event for Notification Service
            from aio_pika import Message
            # We need a reference to the channel or exchange to publish. 
            # Since this function is called from on_message which has the message context, 
            # but usually we need a separate publisher or use the incoming message's channel if strictly consumer.
            # However, for simplicity in this architecture, we might need a global publisher or pass it down.
            # Let's check how health_service does it (it uses a helper).
            # For now, let's assume we can't easily publish *inside* this transaction without a proper event bus.
            # But wait, we are in `on_message` scope in the caller.
            
        session.commit()
        print(f" [Analytics] Processed event for {username}. Generated {len(insights)} insights.")
        
        return insights # Return insights so caller can publish

async def on_message(message: IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        routing_key = message.routing_key
        
        print(f" [Analytics] Received event: {routing_key}")
        
        if "created" in routing_key:
            insights = await process_creation_event(event)
            # ... (Publishing logic kept same, see below) ...
            if insights:
                channel = message.channel
                exchange = await channel.declare_exchange("health_events", passive=True)
                from aio_pika import Message
                for insight in insights:
                    # ... (Publishing code) ...
                    insight_event = {
                        "username": insight.username,
                        "type": insight.type,
                        "severity": insight.severity,
                        "message": insight.message,
                        "timestamp": insight.timestamp.isoformat()
                    }
                    await exchange.publish(
                        Message(
                            body=json.dumps(insight_event).encode(),
                            content_type="application/json"
                        ),
                        routing_key=f"analysis.insight.{insight.type}"
                    )

        elif "updated" in routing_key:
            await process_update_event(event)
        
        elif "deleted" in routing_key:
            await process_deletion_event(event)

async def process_update_event(event: dict):
    username = event.get('username')
    updated_fields = event.get('updated_fields', {})
    old_data = event.get('old_data', {})
    timestamp_str = event.get('timestamp')
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
        date_obj = dt.date()
    except:
        return

    with Session(engine) as session:
        # Get Daily Stats
        stmt = select(DailyHealthStats).where(
            DailyHealthStats.username == username,
            DailyHealthStats.date == date_obj
        )
        daily = session.exec(stmt).first()
        if not daily:
            return # Nothing to update if no stats exist
            
        # 1. Update Steps
        if 'steps' in updated_fields:
            delta = updated_fields['steps'] - old_data.get('steps', 0)
            daily.total_steps += delta
            
        # 2. Update Sleep
        if 'sleep_hours' in updated_fields:
            delta = updated_fields['sleep_hours'] - old_data.get('sleep_hours', 0.0)
            daily.sleep_hours += delta
            
        # 3. Update Heart Rate (Approximate: Update Avg)
        if 'heart_rate' in updated_fields:
            new_hr = updated_fields['heart_rate']
            old_hr = old_data.get('heart_rate')
            if old_hr and daily.heart_rate_count > 0:
                current_total = daily.avg_heart_rate * daily.heart_rate_count
                new_total = current_total - old_hr + new_hr
                daily.avg_heart_rate = new_total / daily.heart_rate_count
                # Note: Min/Max endpoints are hard to correct without full history re-scan
                
        session.add(daily)
        session.commit()
        print(f" [Analytics] Updated stats for {username}")

async def process_deletion_event(event: dict):
    username = event.get('username')
    deleted_record = event.get('deleted_record', {})
    timestamp_str = deleted_record.get('timestamp')
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
        date_obj = dt.date()
    except:
        return

    with Session(engine) as session:
        stmt = select(DailyHealthStats).where(
            DailyHealthStats.username == username,
            DailyHealthStats.date == date_obj
        )
        daily = session.exec(stmt).first()
        if not daily:
            return

        # 1. Subtract Steps
        daily.total_steps -= deleted_record.get('steps', 0)
        
        # 2. Subtract Sleep
        daily.sleep_hours -= deleted_record.get('sleep_hours', 0.0)
        
        # 3. Adjust Heart Rate
        hr = deleted_record.get('heart_rate')
        if hr and daily.heart_rate_count > 0:
            current_total = daily.avg_heart_rate * daily.heart_rate_count
            new_total = current_total - hr
            daily.heart_rate_count -= 1
            if daily.heart_rate_count > 0:
                daily.avg_heart_rate = new_total / daily.heart_rate_count
            else:
                daily.avg_heart_rate = 0.0
                daily.min_heart_rate = None
                daily.max_heart_rate = None

        session.add(daily)
        session.commit()
        print(f" [Analytics] Adjusted stats for {username} (Deletion)")
