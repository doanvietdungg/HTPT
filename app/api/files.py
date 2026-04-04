from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.file import FileCreateRequest, FileCreateResponse, FileDownloadResponse
from app.services.metadata import create_file_metadata, get_file_download_plan
from app.api.deps import get_current_user
from app.models.domain import User

router = APIRouter()

@router.post("/upload/init", response_model=FileCreateResponse)
def init_upload(req: FileCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Client calls this to initialize an upload. 
    NameNode evaluates active nodes and generates a placement plan.
    """
    try:
        return create_file_metadata(db, req, current_user.user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/init/{file_id}", response_model=FileDownloadResponse)
def init_download(file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Client calls this to get chunk location plan to perform download.
    """
    try:
        return get_file_download_plan(db, file_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
