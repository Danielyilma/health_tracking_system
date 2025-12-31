from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import HealthRecord, HealthRecordUpdate
from app.database import get_session
from app.events import publish_event

router = APIRouter()

# Create
@router.post("/data", response_model=HealthRecord)
async def create_health_record(record: HealthRecord, session: Session = Depends(get_session)):
    session.add(record)
    session.commit()
    session.refresh(record)
    
    event_data = {
        "record_id": record.id,
        "username": record.username,
        "steps": record.steps,
        "weight": record.weight,
        "timestamp": record.timestamp.isoformat()
    }
    try:
        await publish_event("created", event_data)
    except Exception as e:
        print(f"Failed to publish event: {e}")

    return record

# List
@router.get("/data", response_model=list[HealthRecord])
def get_health_records(username: str, session: Session = Depends(get_session)):
    statement = select(HealthRecord).where(HealthRecord.username == username)
    results = session.exec(statement)
    return results.all()

# Read (Single)
@router.get("/data/{record_id}", response_model=HealthRecord)
def get_health_record(record_id: int, session: Session = Depends(get_session)):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    return record

# Update
@router.patch("/data/{record_id}", response_model=HealthRecord)
async def update_health_record(record_id: int, update_data: HealthRecordUpdate, session: Session = Depends(get_session)):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(record, key, value)
    
    session.add(record)
    session.commit()
    session.refresh(record)

    # Publish updated event
    event_data = {
        "record_id": record.id,
        "username": record.username,
        "updated_fields": update_dict,
        "timestamp": record.timestamp.isoformat()
    }
    try:
        await publish_event("updated", event_data)
    except Exception as e:
        print(f"Failed to publish event: {e}")

    return record

# Delete
@router.delete("/data/{record_id}")
async def delete_health_record(record_id: int, session: Session = Depends(get_session)):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    username = record.username
    session.delete(record)
    session.commit()

    # Publish deleted event
    event_data = {
        "record_id": record_id,
        "username": username
    }
    try:
        await publish_event("deleted", event_data)
    except Exception as e:
        print(f"Failed to publish event: {e}")

    return {"message": "Record deleted successfully"}
