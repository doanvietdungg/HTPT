from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.database.session import engine
from app.models.base import Base
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.chunks import router as chunks_router
from app.api.nodes import router as nodes_router
from app.api.election import router as election_router
from app.api.lock import router as lock_router
from app.services.heartbeat import send_heartbeat_to_peers
from app.services.recovery import re_replication_daemon
from app.database.session import SessionLocal
from app.models.domain import ClusterNode
import shutil
import asyncio
import datetime

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=f"Mini-HDFS Node ({settings.NODE_ID})",
    description="Mini Distributed File Storage supporting replication, leader election, fault recovery",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(files_router, prefix="/api/files", tags=["files"])
app.include_router(chunks_router, prefix="/api/chunks", tags=["chunks"])
app.include_router(nodes_router, prefix="/api/nodes", tags=["nodes"])
app.include_router(election_router, prefix="/api/election", tags=["election"])
app.include_router(lock_router, prefix="/api/lock", tags=["lock"])

@app.on_event("startup")
async def startup_event():
    print(f"Starting Node {settings.NODE_ID}")
    print(f"Data Dir: {settings.DATA_DIR}")
    print(f"Metadata DB: {settings.DB_URL}")
    print(f"Peers: {settings.PEER_IPS}")
    
    # Self-register this node into the cluster table so it can act immediately
    # even when no peers are online yet
    _self_register()
    
    asyncio.create_task(send_heartbeat_to_peers())
    from app.services.heartbeat import detect_failures_daemon
    from app.services.gossip import sync_metadata_daemon
    asyncio.create_task(detect_failures_daemon())
    asyncio.create_task(sync_metadata_daemon())
    asyncio.create_task(re_replication_daemon())

def _self_register():
    """Register this node into its own ClusterNode table on startup."""
    db = SessionLocal()
    try:
        import os
        data_dir = settings.DATA_DIR
        os.makedirs(data_dir, exist_ok=True)
        total, used, _ = shutil.disk_usage(data_dir)
        
        existing = db.query(ClusterNode).filter(ClusterNode.node_id == settings.NODE_ID).first()
        if existing:
            existing.status = "ALIVE"
            existing.host = settings.MY_IP          # <--- Lấy IP mới nhất
            existing.port = settings.API_PORT       # <--- Lấy Port mới nhất
            existing.last_heartbeat = datetime.datetime.utcnow()
            existing.storage_capacity_total = float(total)
            existing.storage_capacity_used = float(used)
        else:
            node = ClusterNode(
                node_id=settings.NODE_ID,
                node_type="DATANODE",
                host=settings.MY_IP,
                port=settings.API_PORT,
                status="ALIVE",
                role="FOLLOWER",
                term=0,
                last_heartbeat=datetime.datetime.utcnow(),
                storage_capacity_total=float(total),
                storage_capacity_used=float(used),
                cpu_load=0.0,
                network_score=1.0,
            )
            db.add(node)
        db.commit()
        print(f"[Startup] Self-registered node '{settings.NODE_ID}' as ALIVE.")
    except Exception as e:
        print(f"[Startup] Self-register failed: {e}")
    finally:
        db.close()

# Mount the static frontend
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/ui/")
