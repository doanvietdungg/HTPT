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
            # In a real system, we only run this if we are the LEADER
            election_state = db.query(ClusterNode).filter(ClusterNode.node_id == settings.NODE_ID, ClusterNode.status == "ALIVE").first()
            if True: # Simulating that we are tracking under-replicated chunks 
                
                # Find all COMMITTED chunks
                active_chunks = db.query(ChunkEntry).filter(ChunkEntry.status == "COMMITTED").all()
                for ck in active_chunks:
                    # Count ALIVE replicas
                    alive_replicas = db.query(ChunkReplica).join(ClusterNode, ChunkReplica.node_id == ClusterNode.node_id)\
                        .filter(ChunkReplica.chunk_id == ck.chunk_id, ClusterNode.status == "ALIVE").count()
                    
                    file_entry = db.query(FileEntry).filter(FileEntry.file_id == ck.file_id).first()
                    if file_entry and alive_replicas < file_entry.replication_factor:
                        print(f"Warning: Chunk {ck.chunk_id} is under-replicated ({alive_replicas}/{file_entry.replication_factor}). Re-replication needed.")
                        # This is where we would automatically trigger a background task to fetch the chunk from an active node 
                        # and forward it to a new node using the calculate_chunk_placement logic.
                        
            db.close()
        except Exception as e:
            print(f"Recovery daemon error: {e}")
            
        await asyncio.sleep(10) # Check every 10 seconds
