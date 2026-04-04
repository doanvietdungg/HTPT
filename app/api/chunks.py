from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.storage import save_chunk_locally, forward_chunk_to_replica
from app.models.domain import ChunkReplica, FileEntry
import uuid
import datetime
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
async def upload_chunk(
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    secondary_nodes: Optional[str] = Form(None), # Comma separated IPs of secondaries
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Called by Client. This node acts as Primary DataNode.
    """
    # 1. Save locally
    file_path = save_chunk_locally(file_id, chunk_index, file)
    
    # Update local DB metadata for replica
    ck_id = f"{file_id}_ck_{chunk_index}"
    replica = ChunkReplica(
        replica_id=str(uuid.uuid4()),
        chunk_id=ck_id,
        node_id=settings.NODE_ID,
        replica_order=0,
        replica_state="SYNCED",
        stored_path=file_path,
        last_verified_at=datetime.datetime.utcnow()
    )
    db.add(replica)
    db.commit()

    # 2. Pipeline to secondaries
    failed_forwards = []
    if secondary_nodes:
        nodes = [n.strip() for n in secondary_nodes.split(",") if n.strip()]
        for idx, next_node in enumerate(nodes):
            success = await forward_chunk_to_replica(file_id, chunk_index, file_path, next_node)
            if not success:
                failed_forwards.append(next_node)
    
    if failed_forwards:
        return {"status": "partial", "message": "Saved locally but failed to pipeline to some replicas", "failed": failed_forwards}
        
    return {"status": "success", "message": "Chunk saved and replicated"}


@router.post("/replica")
async def receive_replica_chunk(
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Called by Primary DataNode to replicate chunk.
    """
    file_path = save_chunk_locally(file_id, chunk_index, file)
    
    ck_id = f"{file_id}_ck_{chunk_index}"
    replica = ChunkReplica(
        replica_id=str(uuid.uuid4()),
        chunk_id=ck_id,
        node_id=settings.NODE_ID,
        replica_order=1, # secondary
        replica_state="SYNCED",
        stored_path=file_path,
        last_verified_at=datetime.datetime.utcnow()
    )
    db.add(replica)
    db.commit()
    
    return {"status": "success"}

@router.get("/download/{chunk_id}", response_class=FileResponse)
def download_chunk(chunk_id: str, db: Session = Depends(get_db)):
    """
    Called by Client. Returns the physical chunk binary data.
    """
    replica = db.query(ChunkReplica).filter(ChunkReplica.chunk_id == chunk_id, ChunkReplica.node_id == settings.NODE_ID).first()
    if not replica:
        raise HTTPException(status_code=404, detail="Chunk not found on this node")
        
    # Attempt to sniff the original file extension to help the client auto-download format
    download_name = chunk_id
    try:
        if "_ck_" in chunk_id:
            file_id = chunk_id.split("_ck_")[0]
            f_entry = db.query(FileEntry).filter(FileEntry.file_id == file_id).first()
            if f_entry and f_entry.file_name:
                import os
                ext = os.path.splitext(f_entry.file_name)[1] # get .mp4, .jpg...
                if ext:
                    download_name = f"{chunk_id}{ext}"
    except Exception:
        pass
        
    return FileResponse(path=replica.stored_path, filename=download_name, media_type='application/octet-stream')
