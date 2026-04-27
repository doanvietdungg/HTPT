from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx
import mimetypes
import os
import urllib.parse

from app.database.session import get_db, SessionLocal
from app.schemas.file import FileCreateRequest, FileCreateResponse, FileDownloadResponse, FileMetadata
from app.services.metadata import create_file_metadata, get_file_download_plan
from app.services.lock import acquire_lock, release_lock
from app.models.domain import FileEntry
from app.api.deps import get_current_user
import asyncio
import uuid
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

@router.get("/s3/{file_id}")
async def s3_object_gateway(file_id: str, slow: bool = False, db: Session = Depends(get_db)):
    """
    S3 Object Storage Proxy. 
    Internally queries the Download Plan, loops through active node IPs, 
    and streams back raw binaries as a single continuous file.
    """
    try:
        plan = get_file_download_plan(db, file_id)
        
        # Sniff mimetype
        mime_type, _ = mimetypes.guess_type(plan.file_name)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        async def stream_chunks():
            stream_db = SessionLocal()
            client_id = f"dl_{uuid.uuid4()}"
            lock = None
            try:
                # Acquire SHARED lock
                lock = acquire_lock(stream_db, file_id, client_id, "system", "SHARED")
                
                async with httpx.AsyncClient() as client:
                    for chunk in plan.chunks:
                        if not chunk.node_ips:
                            continue
                            
                        target_host_port = chunk.node_ips[0]
                        url = f"http://{target_host_port}/api/chunks/download/{chunk.chunk_id}"
                        
                        try:
                            async with client.stream("GET", url) as response:
                                if response.status_code == 200:
                                    async for content in response.aiter_bytes():
                                        yield content
                                        if slow:
                                            await asyncio.sleep(1) # Slow down for testing
                        except Exception as e:
                            print(f"Failed to fetch chunk {chunk.chunk_id} from {target_host_port}: {e}")
            finally:
                if lock:
                    try:
                        release_lock(stream_db, lock.lock_id, client_id)
                    except Exception as e:
                        print(f"Error releasing lock: {e}")
                stream_db.close()
                        
        encoded_name = urllib.parse.quote(plan.file_name)
        headers = {
            "Content-Disposition": f"inline; filename*=utf-8''{encoded_name}"
        }
                        
        return StreamingResponse(stream_chunks(), media_type=mime_type, headers=headers)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=list[FileMetadata])
def list_files(db: Session = Depends(get_db)):
    """
    Returns list of all files in system.
    """
    files = db.query(FileEntry).filter(FileEntry.status != "DELETED").all()
    return files

@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a file. Requires EXCLUSIVE lock.
    """
    client_id = f"del_{uuid.uuid4()}"
    lock = acquire_lock(db, file_id, client_id, current_user.user_id, "EXCLUSIVE")
    try:
        file_entry = db.query(FileEntry).filter(FileEntry.file_id == file_id).first()
        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found")
            
        import datetime
        file_entry.status = "DELETED"
        file_entry.updated_at = datetime.datetime.utcnow()
        db.commit()
        return {"status": "success", "message": "File deleted successfully"}
    finally:
        release_lock(db, lock.lock_id, client_id)
