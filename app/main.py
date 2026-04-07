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
import asyncio

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
    asyncio.create_task(send_heartbeat_to_peers())
    asyncio.create_task(re_replication_daemon())

# Mount the static frontend
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/ui/")
