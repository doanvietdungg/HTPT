import asyncio
import httpx
import shutil
import psutil
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.core.config import settings
from app.models.domain import ClusterNode
import datetime

async def send_heartbeat_to_peers():
    """
    Background task to periodically broadcast heartbeat to peers.
    """
    peers = [p.strip() for p in settings.PEER_IPS.split(",") if p.strip()]
    if not peers:
        return

    while True:
        try:
            # Gather metrics
            total, used, free = shutil.disk_usage(settings.DATA_DIR)
            cpu_load = psutil.cpu_percent(interval=None) / 100.0
            
            async with httpx.AsyncClient() as client:
                for peer in peers:
                    url = f"http://{peer}/api/nodes/heartbeat"
                    params = {
                        "node_id": settings.NODE_ID,
                        "capacity": float(total),
                        "used": float(used),
                        "cpu_load": cpu_load
                    }
                    try:
                        await client.post(url, params=params, timeout=2.0)
                    except Exception:
                        pass # Ignore if peer is down
                        
            # Use a local session to perform failure detection on other nodes
            detect_failures()
        except Exception as e:
            print(f"Heartbeat loop error: {e}")
            
        await asyncio.sleep(settings.HEARTBEAT_INTERVAL)

def detect_failures():
    """
    Check last_heartbeat of nodes and mark them DEAD if > timeout.
    """
    db = SessionLocal()
    try:
        nodes = db.query(ClusterNode).filter(ClusterNode.node_id != settings.NODE_ID).all()
        now = datetime.datetime.utcnow()
        for node in nodes:
            if node.last_heartbeat:
                delta = (now - node.last_heartbeat).total_seconds()
                if delta > settings.ELECTION_TIMEOUT and node.status == "ALIVE":
                    node.status = "DEAD"
                    print(f"Node {node.node_id} detected as DEAD.")
                    # Trigger re-replication logic here in future
        db.commit()
    finally:
        db.close()
