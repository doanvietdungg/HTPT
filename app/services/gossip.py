import asyncio
import httpx
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.core.config import settings
from app.models.domain import FileEntry, ChunkEntry, ChunkReplica
from app.schemas.metadata_sync import MetadataDumpResponse

async def sync_metadata_daemon():
    """
    Background Task to achieve Eventual Consistency for Metadata.
    Periodically fetches metadata from all PEER_IPS and merges into the local DB.
    """
    while True:
        peers = [p.strip() for p in settings.PEER_IPS.split(",") if p.strip()]
        if peers:
            async with httpx.AsyncClient() as client:
                for peer in peers:
                    url = f"http://{peer}/api/nodes/metadata/dump"
                    try:
                        resp = await client.get(url, timeout=5.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            _merge_metadata(data)
                    except Exception as e:
                        print(f"[Gossip] Failed to sync metadata from {peer}: {e}")
        
        # Ping every 10 seconds
        await asyncio.sleep(10)

from app.schemas.metadata_sync import FileEntryDump, ChunkEntryDump, ChunkReplicaDump

def _merge_metadata(data: dict):
    """
    Merge the incoming metadata into the local SQLite/MySQL Database using SQLAlchemy's object merge logic.
    Since we removed hard ForeignKey constraints earlier, we can merge records in any order safely!
    """
    db = SessionLocal()
    try:
        # Merge Files
        for f_data in data.get("files", []):
            validated = FileEntryDump(**f_data).dict()
            db.merge(FileEntry(**validated))
            
        # Merge Chunks
        for c_data in data.get("chunks", []):
            validated = ChunkEntryDump(**c_data).dict()
            db.merge(ChunkEntry(**validated))
            
        # Merge Replicas
        for r_data in data.get("replicas", []):
            validated = ChunkReplicaDump(**r_data).dict()
            db.merge(ChunkReplica(**validated))
            
        db.commit()
    except Exception as e:
        print(f"[Gossip] DB Merge Exception: {e}")
        db.rollback()
    finally:
        db.close()
