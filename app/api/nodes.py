from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database.session import get_db
from app.models.domain import ClusterNode
import datetime

router = APIRouter()

@router.post("/heartbeat")
def receive_heartbeat(
    node_id: str,
    capacity: float,
    used: float,
    cpu_load: float,
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: Session = Depends(get_db)
):
    node = db.query(ClusterNode).filter(ClusterNode.node_id == node_id).first()
    if not node:
        # Auto-register peer node when it pings us for the first time
        node = ClusterNode(
            node_id=node_id,
            host=host,
            port=port,
            status="ALIVE",
            role="FOLLOWER",
            term=0,
            storage_capacity_total=capacity,
            storage_capacity_used=used,
            cpu_load=cpu_load,
            network_score=1.0,
            last_heartbeat=datetime.datetime.utcnow()
        )
        db.add(node)
    else:
        node.status = "ALIVE"
        if host:
            node.host = host
        if port:
            node.port = port
        node.storage_capacity_total = capacity
        node.storage_capacity_used = used
        node.cpu_load = cpu_load
        node.last_heartbeat = datetime.datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@router.get("/topology")
def get_topology(db: Session = Depends(get_db)):
    """
    Returns node_id → host:port mapping for all ALIVE nodes.
    Frontend uses this to route chunk uploads directly to the correct node.
    """
    nodes = db.query(ClusterNode).filter(ClusterNode.status == "ALIVE").all()
    return {
        n.node_id: {
            "host": n.host or n.node_id,
            "port": n.port or 8000
        }
        for n in nodes
    }
