from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx
import mimetypes
import os
import urllib.parse

from app.database.session import get_db
from app.schemas.file import FileCreateRequest, FileCreateResponse, FileDownloadResponse, FileMetadata
from app.services.metadata import create_file_metadata, get_file_download_plan
from app.models.domain import FileEntry
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

@router.get("/s3/{file_id}")
async def s3_object_gateway(file_id: str, db: Session = Depends(get_db)):
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
            async with httpx.AsyncClient() as client:
                for chunk in plan.chunks:
                    if not chunk.node_ips:
                        # Missing entirely
                        continue
                        
                    # Pick the first active replica for this chunk
                    target_host_port = chunk.node_ips[0]
                    # target_host_port is fetched strictly from the DB topology (e.g. '127.0.0.1:8000')
                    url = f"http://{target_host_port}/api/chunks/download/{chunk.chunk_id}"
                    
                    try:
                        async with client.stream("GET", url) as response:
                            if response.status_code == 200:
                                async for content in response.aiter_bytes():
                                    yield content
                    except Exception as e:
                        print(f"Failed to fetch chunk {chunk.chunk_id} from {target_ip}: {e}")
                        # In production: fallback to chunk.node_ips[1] etc.
                        
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
    files = db.query(FileEntry).all()
    return files
