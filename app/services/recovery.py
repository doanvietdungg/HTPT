import asyncio
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.domain import FileEntry, ChunkEntry, ChunkReplica, ClusterNode
from app.services.metadata import generate_placement_plan, get_active_nodes
from app.core.config import settings
import datetime

async def re_replication_daemon():
    """
    Background daemon running on the Leader to detect under-replicated chunks
    and trigger re-replication.
    """
    while True:
        try:
            db = SessionLocal()
            
            # Find all chunks (including ORPHAN since upload flow doesn't set COMMITTED yet)
            active_chunks = db.query(ChunkEntry).all()
            for ck in active_chunks:
                    file_entry = db.query(FileEntry).filter(FileEntry.file_id == ck.file_id).first()
                    if not file_entry:
                        continue
                        
                    # Count ALIVE replicas
                    alive_replicas = db.query(ChunkReplica).join(ClusterNode, ChunkReplica.node_id == ClusterNode.node_id)\
                        .filter(ChunkReplica.chunk_id == ck.chunk_id, ClusterNode.status == "ALIVE").count()
                    
                    if alive_replicas < file_entry.replication_factor:
                        # Find source nodes (ALIVE and HAS the chunk)
                        alive_nodes_with_chunk = db.query(ClusterNode).join(ChunkReplica, ClusterNode.node_id == ChunkReplica.node_id)\
                            .filter(ChunkReplica.chunk_id == ck.chunk_id, ClusterNode.status == "ALIVE")\
                            .order_by(ClusterNode.node_id).all()
                        
                        if not alive_nodes_with_chunk:
                            continue
                            
                        # Deterministic orchestrator: Only the alive node with the smallest node_id that HAS the chunk triggers the pull
                        if alive_nodes_with_chunk[0].node_id != settings.NODE_ID:
                            continue
                            
                        print(f"[Recovery] Chunk {ck.chunk_id} is under-replicated ({alive_replicas}/{file_entry.replication_factor}). Triggering pull...")
                        source_node = alive_nodes_with_chunk[0]
                            
                        # Find destination node (ALIVE and DOES NOT have the chunk)
                        dest_node = None
                        replica_node_ids = [n.node_id for n in alive_nodes_with_chunk]
                        all_alive_nodes = db.query(ClusterNode).filter(ClusterNode.status == "ALIVE").order_by(ClusterNode.node_id).all()
                        for node in all_alive_nodes:
                            if node.node_id not in replica_node_ids:
                                dest_node = node
                                break
                                
                        if source_node and dest_node:
                            import httpx
                            # Trigger the pull
                            try:
                                dest_host = dest_node.host or dest_node.node_id
                                dest_port = dest_node.port or 8000
                                url = f"http://{dest_host}:{dest_port}/api/chunks/pull"
                                
                                source_host = source_node.host or source_node.node_id
                                source_port = source_node.port or 8000
                                source_ip = f"{source_host}:{source_port}"
                                
                                data = {"chunk_id": ck.chunk_id, "source_node_ip": source_ip}
                                
                                print(f"[Recovery] Ordering {dest_node.node_id} to pull {ck.chunk_id} from {source_node.node_id}")
                                async with httpx.AsyncClient() as client:
                                    resp = await client.post(url, data=data, timeout=10.0)
                                    if resp.status_code == 200:
                                        print(f"[Recovery] Success: {resp.json()}")
                                    else:
                                        print(f"[Recovery] Failed to order pull: {resp.status_code} - {resp.text}")
                            except Exception as pull_e:
                                print(f"[Recovery] Pull HTTP exception: {pull_e}")
                        else:
                            print(f"[Recovery] Cannot re-replicate {ck.chunk_id}: No destination available.")
            db.close()
        except Exception as e:
            print(f"Recovery daemon error: {e}")
            
        await asyncio.sleep(10) # Check every 10 seconds
