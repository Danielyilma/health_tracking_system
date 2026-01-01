import json
from aio_pika import IncomingMessage
from sqlmodel import Session
from app.database import engine
from app.models import Notification

from app.manager import manager

async def save_notification(username: str, message: str, type: str):
    """Helper to save notification to DB and Push to WS"""
    with Session(engine) as session:
        notif = Notification(username=username, message=message, type=type)
        session.add(notif)
        session.commit()
        session.refresh(notif)
        print(f" [Notification] Saved {type}: {message}")
        
    # Push to WebSocket
    payload = json.dumps({
        "type": type,
        "message": message,
        "timestamp": notif.timestamp.isoformat()
    })
    await manager.send_personal_message(payload, username)

async def on_message(message: IncomingMessage):
    async with message.process():
        event = json.loads(message.body)
        routing_key = message.routing_key
        
        print(f" [Notification] Received event: {routing_key}")
        
        username = event.get('username')
        if not username:
            return

        # 1. New Health Insights (Alerts)
        if "analysis.insight" in routing_key:
            # event = {username, type, severity, message, timestamp}
            # We treat insights as "Alerts" or "Recommendations"
            insight_type = event.get('type')
            severity = event.get('severity')
            msg_text = event.get('message')
            
            # Map severity/type to Notification type
            notif_type = "Alert" if severity in ["WARNING", "CRITICAL"] else "Info"
            
            await save_notification(username, msg_text, notif_type)

        # 2. Health Record Updates (System Info)
        elif "created" in routing_key:
            # Construct detailed message
            parts = []
            if event.get('steps'): parts.append(f"Steps: {event.get('steps')}")
            if event.get('heart_rate'): parts.append(f"HR: {event.get('heart_rate')}bpm")
            if event.get('sleep_hours'): parts.append(f"Sleep: {event.get('sleep_hours')}h")
            if event.get('weight'): parts.append(f"Weight: {event.get('weight')}kg")
            if event.get('blood_pressure'): parts.append(f"BP: {event.get('blood_pressure')}")
            if event.get('blood_sugar'): parts.append(f"Sugar: {event.get('blood_sugar')}")
            if event.get('body_temperature'): parts.append(f"Temp: {event.get('body_temperature')}C")
            
            details = ", ".join(parts) if parts else "No metrics"
            await save_notification(username, f"New Health Data: {details}", "System")
            
        elif "updated" in routing_key:
            changes = event.get('updated_fields', {})
            # Format changes: "Steps 500->1000"
            old_data = event.get('old_data', {})
            
            parts = []
            for field, new_val in changes.items():
                old_val = old_data.get(field, "?")
                parts.append(f"{field}: {old_val} -> {new_val}")
            
            msg = "Record Updated: " + ", ".join(parts) if parts else "Record Updated"
            await save_notification(username, msg, "System")

        elif "deleted" in routing_key:
            record_data = event.get('deleted_record', {})
            date_part = record_data.get('timestamp', '').split('T')[0]
            
            parts = []
            if record_data.get('steps'): parts.append(f"Steps: {record_data['steps']}")
            if record_data.get('heart_rate'): parts.append(f"HR: {record_data['heart_rate']}")
            
            details = ", ".join(parts)
            await save_notification(username, f"Record Deleted ({date_part}): {details}", "System")

