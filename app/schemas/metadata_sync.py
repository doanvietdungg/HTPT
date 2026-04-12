from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FileEntryDump(BaseModel):
    file_id: str
    file_name: str
    logical_path: str
    owner_user_id: Optional[str]
    size_bytes: int
    chunk_size: int
    total_chunks: int
    replication_factor: int
    status: str
    created_at: datetime
    updated_at: datetime

class ChunkEntryDump(BaseModel):
    chunk_id: str
    file_id: str
    chunk_index: int
    primary_node_id: str
    chunk_size: int
    checksum_chunk: Optional[str]
    status: str
    created_at: datetime

class ChunkReplicaDump(BaseModel):
    replica_id: str
    chunk_id: str
    node_id: str
    replica_order: int
    replica_state: str
    stored_path: str
    last_verified_at: Optional[datetime]

class MetadataDumpResponse(BaseModel):
    files: List[FileEntryDump]
    chunks: List[ChunkEntryDump]
    replicas: List[ChunkReplicaDump]
