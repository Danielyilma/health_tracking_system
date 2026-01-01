from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from app.database import get_session
from app.models import Notification, Reminder

router = APIRouter()

@router.get("/list/{username}", response_model=List[Notification])
def get_notifications(username: str, session: Session = Depends(get_session)):
    statement = select(Notification).where(Notification.username == username).order_by(Notification.timestamp.desc())
    return session.exec(statement).all()

@router.post("/{notification_id}/read")
def mark_read(notification_id: int, session: Session = Depends(get_session)):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    session.add(notification)
    session.commit()
    return {"message": "Marked as read"}

@router.post("/reminders", response_model=Reminder)
def create_reminder(reminder: Reminder, session: Session = Depends(get_session)):
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder

from fastapi import WebSocket, WebSocketDisconnect
from app.manager import manager

@router.websocket("/ws/{username}")
@router.websocket("/ws/{username}/")
async def websocket_endpoint(websocket: WebSocket, username: str):
    print(f" [API] WebSocket connection attempt for {username}...")
    await manager.connect(websocket, username)
    try:
        while True:
            # Just keep connection open. 
            # In a real app we might handle incoming messages (e.g. read receipts)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)
