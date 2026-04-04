from sqlalchemy.orm import Session
from app.models.domain import FileLock
from fastapi import HTTPException
import uuid
import datetime

def acquire_lock(db: Session, file_id: str, client_id: str, user_id: str, lock_type: str) -> FileLock:
    """
    Lock Type: 'SHARED' or 'EXCLUSIVE'
    """
    # Auto-release expired locks
    now = datetime.datetime.utcnow()
    expired_locks = db.query(FileLock).filter(FileLock.file_id == file_id, FileLock.expire_at < now, FileLock.status == "ACQUIRED").all()
    for l in expired_locks:
        l.status = "RELEASED"
    db.commit()

    active_locks = db.query(FileLock).filter(FileLock.file_id == file_id, FileLock.status == "ACQUIRED").all()
    
    if lock_type == "EXCLUSIVE":
        if len(active_locks) > 0:
            raise HTTPException(status_code=409, detail="File is currently locked")
    elif lock_type == "SHARED":
        for l in active_locks:
            if l.lock_type == "EXCLUSIVE":
                raise HTTPException(status_code=409, detail="File is exclusively locked for writing")

    new_lock = FileLock(
        lock_id=str(uuid.uuid4()),
        file_id=file_id,
        lock_type=lock_type,
        owner_client_id=client_id,
        owner_user_id=user_id,
        acquired_at=now,
        expire_at=now + datetime.timedelta(seconds=30), # 30s TTL
        status="ACQUIRED"
    )
    db.add(new_lock)
    db.commit()
    db.refresh(new_lock)
    return new_lock

def release_lock(db: Session, lock_id: str, client_id: str):
    lock = db.query(FileLock).filter_by(lock_id=lock_id).first()
    if not lock or lock.owner_client_id != client_id:
        raise HTTPException(status_code=403, detail="Not authorized to release this lock")
        
    lock.status = "RELEASED"
    db.commit()
    return True
