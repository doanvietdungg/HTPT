from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FileCreateRequest(BaseModel):
    file_name: str
    size_bytes: int
    logical_path: str = "/"

class ChunkPlacement(BaseModel):
    chunk_index: int
    primary_node: str
    secondary_nodes: List[str]

class FileCreateResponse(BaseModel):
    file_id: str
    file_name: str
    chunk_size: int
    total_chunks: int
    placement_plan: List[ChunkPlacement] 

class ChunkLocation(BaseModel):
    chunk_index: int
    chunk_id: str
    node_ips: List[str] # List of IPs of nodes that hold this chunk and are ALIVE

class FileDownloadResponse(BaseModel):
    file_id: str
    file_name: str
    total_chunks: int
    chunks: List[ChunkLocation]

class FileMetadata(BaseModel):
    file_id: str
    file_name: str
    size_bytes: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
