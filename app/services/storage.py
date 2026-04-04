import os
import shutil
import httpx
from fastapi import UploadFile, HTTPException
from typing import List
from app.core.config import settings

def save_chunk_locally(file_id: str, chunk_index: int, upload_file: UploadFile) -> str:
    # Ensure data directory exists
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    file_path = os.path.join(settings.DATA_DIR, f"{file_id}_ck_{chunk_index}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save chunk logically: {str(e)}")

async def forward_chunk_to_replica(file_id: str, chunk_index: int, file_path: str, next_node_ip: str) -> bool:
    """
    Pipelining: Primary node forwards the chunk to the secondary node
    """
    # Assuming next_node_ip contains IP:PORT
    url = f"http://{next_node_ip}/api/chunks/replica"
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {'file': (f"{file_id}_ck_{chunk_index}", f, 'application/octet-stream')}
                data = {'file_id': file_id, 'chunk_index': chunk_index}
                
                resp = await client.post(url, data=data, files=files, timeout=60.0)
                if resp.status_code == 200:
                    return True
        return False
    except Exception:
        return False
