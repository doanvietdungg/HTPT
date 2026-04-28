import math
import uuid
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.domain import FileEntry, ChunkEntry, ClusterNode, ChunkReplica, AuditLog
from app.schemas.file import FileCreateRequest, FileCreateResponse, ChunkPlacement, FileDownloadResponse, ChunkLocation
from app.core.config import settings
from fastapi import HTTPException

def get_active_nodes(db: Session, min_free_space: int = 0) -> List[ClusterNode]:
    # In reality, filter by ALIVE and sufficient capacity
    nodes = db.query(ClusterNode).filter(
        ClusterNode.status == "ALIVE"
    ).all()
    # Filter space
    valid_nodes = []
    for n in nodes:
        free_space = n.storage_capacity_total - n.storage_capacity_used
        if free_space > min_free_space:
            valid_nodes.append(n)
    return valid_nodes

def score_node(node: ClusterNode) -> float:
    # W1 * free_space + W2 * (1-cpu_load) + W3 * network_score
    free_ratio = 1.0
    if node.storage_capacity_total > 0:
         free_ratio = (node.storage_capacity_total - node.storage_capacity_used) / node.storage_capacity_total
    
    # Simple scoring for implementation
    score = (0.5 * free_ratio) + (0.3 * (1.0 - node.cpu_load)) + (0.2 * node.network_score)
    return score

def generate_placement_plan(db: Session, total_chunks: int, chunk_size: int, replication_factor: int) -> List[ChunkPlacement]:
    # 1. Get active nodes that can hold a chunk
    valid_nodes = get_active_nodes(db, chunk_size)
    
    if len(valid_nodes) == 0:
        raise HTTPException(status_code=507, detail="No active nodes available for storage")

    # Gracefully degrade replication factor if fewer nodes are available
    # e.g. only 1 node alive → replication_factor becomes 1 (no replica)
    effective_rf = min(replication_factor, len(valid_nodes))
    if effective_rf < replication_factor:
        print(f"[Warning] Only {len(valid_nodes)} node(s) available. "
              f"Replication factor degraded from {replication_factor} → {effective_rf}")
        
    # 2. Sort nodes by score descending
    valid_nodes.sort(key=lambda x: score_node(x), reverse=True)
    
    # 3. Create plan
    plan = []
    for i in range(total_chunks):
        primary_idx = i % len(valid_nodes)
        primary_node = valid_nodes[primary_idx].node_id
        
        secondary_nodes = []
        for j in range(1, effective_rf):
            sec_idx = (primary_idx + j) % len(valid_nodes)
            secondary_nodes.append(valid_nodes[sec_idx].node_id)
            
        plan.append(ChunkPlacement(
            chunk_index=i,
            primary_node=primary_node,
            secondary_nodes=secondary_nodes
        ))
        
    return plan


def create_file_metadata(db: Session, req: FileCreateRequest, user_id: str) -> FileCreateResponse:
    # 1. Compute chunks
    total_chunks = math.ceil(req.size_bytes / settings.CHUNK_SIZE)
    if total_chunks == 0:
        total_chunks = 1 # handle empty file
        
    file_id = str(uuid.uuid4())
    
    # 2. Generate placement plan
    placement_plan = generate_placement_plan(
        db=db, 
        total_chunks=total_chunks, 
        chunk_size=settings.CHUNK_SIZE, 
        replication_factor=settings.REPLICATION_FACTOR
    )
    
    # 3. Create FileEntry
    new_file = FileEntry(
        file_id=file_id,
        file_name=req.file_name,
        logical_path=req.logical_path,
        owner_user_id=user_id,
        size_bytes=req.size_bytes,
        chunk_size=settings.CHUNK_SIZE,
        total_chunks=total_chunks,
        replication_factor=settings.REPLICATION_FACTOR,
        status="UPLOADING"
    )
    db.add(new_file)
    db.flush() # Force insert of FileEntry before chunks to satisfy MySQL FKs
    
    # 4. Create ChunkEntries (Orphans until committed)
    for p in placement_plan:
        chunk_id = f"{file_id}_ck_{p.chunk_index}"
        ck = ChunkEntry(
            chunk_id=chunk_id,
            file_id=file_id,
            chunk_index=p.chunk_index,
            primary_node_id=p.primary_node,
            chunk_size=settings.CHUNK_SIZE, # Can be smaller for last chunk, simplifying for now
            status="ORPHAN"
        )
        db.add(ck)
        
    db.commit()
    
    # Record origin node in AuditLog (local only, not gossiped)
    audit = AuditLog(
        audit_id=str(uuid.uuid4()),
        user_id=user_id,
        action_type="UPLOAD_INIT",
        file_id=file_id,
        target_node_id=settings.NODE_ID,
        result="SUCCESS",
        detail="File initialization"
    )
    db.add(audit)
    db.commit()
    
    return FileCreateResponse(
        file_id=file_id,
        file_name=req.file_name,
        chunk_size=settings.CHUNK_SIZE,
        total_chunks=total_chunks,
        placement_plan=placement_plan,
        cdn_url=f"http://localhost:{settings.API_PORT}/api/files/s3/{file_id}"
    )

def get_file_download_plan(db: Session, file_id: str) -> FileDownloadResponse:
    file_entry = db.query(FileEntry).filter(FileEntry.file_id == file_id).first()
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found")
        
    chunks = db.query(ChunkEntry).filter(ChunkEntry.file_id == file_id).order_by(ChunkEntry.chunk_index).all()
    
    chunk_locations = []
    for ck in chunks:
        # Find replicas that are on ALIVE nodes
        replicas = db.query(ChunkReplica).join(ClusterNode, ChunkReplica.node_id == ClusterNode.node_id)\
            .filter(ChunkReplica.chunk_id == ck.chunk_id, ClusterNode.status == "ALIVE").all()
            
        ips = []
        for r in replicas:
            n = db.query(ClusterNode).filter(ClusterNode.node_id == r.node_id).first()
            if n and n.host:
                ips.append(f"{n.host}:{n.port}")
            else:
                ips.append(r.node_id)
            
        if not ips:
            # Fallback to primary node if no replicas registered yet (e.g. testing)
            n_pri = db.query(ClusterNode).filter(ClusterNode.node_id == ck.primary_node_id).first()
            if n_pri and n_pri.host:
                ips.append(f"{n_pri.host}:{n_pri.port}")
            else:
                ips.append(ck.primary_node_id)
            
        chunk_locations.append(ChunkLocation(
            chunk_index=ck.chunk_index,
            chunk_id=ck.chunk_id,
            node_ips=ips
        ))
        
    return FileDownloadResponse(
        file_id=file_id,
        file_name=file_entry.file_name,
        total_chunks=file_entry.total_chunks,
        chunks=chunk_locations
    )
