from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.domain import ClusterNode
import datetime

router = APIRouter()

@router.post("/heartbeat")
def receive_heartbeat(node_id: str, capacity: float, used: float, cpu_load: float, db: Session = Depends(get_db)):
    node = db.query(ClusterNode).filter(ClusterNode.node_id == node_id).first()
    if not node:
        # Auto-register node if unknown
        node = ClusterNode(
            node_id=node_id,
            status="ALIVE",
            storage_capacity_total=capacity,
            storage_capacity_used=used,
            cpu_load=cpu_load,
            last_heartbeat=datetime.datetime.utcnow()
        )
        db.add(node)
    else:
        node.status = "ALIVE"
        node.storage_capacity_total = capacity
        node.storage_capacity_used = used
        node.cpu_load = cpu_load
        node.last_heartbeat = datetime.datetime.utcnow()
    db.commit()
    return {"status": "ok"}
