import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.models import HealthRecord, HealthRecordCreate, HealthRecordUpdate
from app.database import get_session
from app.events import publish_event
from jose import JWTError, jwt

router = APIRouter()

# Configuration (should match Auth Service)
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # This URL likely needs to be full path or relative to gateway if used in Swagger from here, but mostly for Depends

async def get_current_username(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Create
@router.post("/data", response_model=HealthRecord)
async def create_health_record(
    record_create: HealthRecordCreate, 
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    record = HealthRecord(**record_create.dict(), username=username)
    
    session.add(record)
    session.commit()
    session.refresh(record)
    
    event_data = {
        "record_id": record.id,
        "username": record.username,
        "steps": record.steps,
        "weight": record.weight,
        "sleep_hours": record.sleep_hours,
        "heart_rate": record.heart_rate,
        "blood_pressure": record.blood_pressure,
        "blood_sugar": record.blood_sugar,
        "body_temperature": record.body_temperature,
        "timestamp": record.timestamp.isoformat()
    }
    try:
        await publish_event("created", event_data)
    except Exception as e:
        print(f"Failed to publish event: {e}")

    return record

# List
@router.get("/data", response_model=list[HealthRecord])
def get_health_records(
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    statement = select(HealthRecord).where(HealthRecord.username == username)
    results = session.exec(statement)
    return results.all()

# Read (Single)
@router.get("/data/{record_id}", response_model=HealthRecord)
def get_health_record(
    record_id: int, 
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    if record.username != username:
         raise HTTPException(status_code=403, detail="Not authorized to access this record")
    return record

# Update
@router.patch("/data/{record_id}", response_model=HealthRecord)
async def update_health_record(
    record_id: int, 
    update_data: HealthRecordUpdate, 
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    if record.username != username:
         raise HTTPException(status_code=403, detail="Not authorized to access this record")
    
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
async def delete_health_record(
    record_id: int, 
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    record = session.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    if record.username != username:
         raise HTTPException(status_code=403, detail="Not authorized to access this record")
    
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
