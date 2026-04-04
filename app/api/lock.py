from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.lock import acquire_lock, release_lock
from app.api.deps import get_current_user
from app.models.domain import User

router = APIRouter()

@router.post("/acquire")
def api_acquire_lock(
    file_id: str, 
    client_id: str, 
    lock_type: str = Query(..., description="SHARED or EXCLUSIVE"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lock = acquire_lock(db, file_id, client_id, current_user.user_id, lock_type)
    return {"lock_id": lock.lock_id, "status": "ACQUIRED", "expire_at": lock.expire_at}

@router.post("/release")
def api_release_lock(
    lock_id: str,
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    release_lock(db, lock_id, client_id)
    return {"status": "RELEASED"}
