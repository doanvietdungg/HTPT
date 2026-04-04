from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = f"""
    <html>
        <head>
            <title>Mini-HDFS Dashboard - {settings.NODE_ID}</title>
            <style>
                body {{ font-family: Arial; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                .card {{ border: 1px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Mini-HDFS Node: {settings.NODE_ID}</h1>
            <div class="card">
                <h2>Node Information</h2>
                <p><strong>IP:</strong> {settings.MY_IP}</p>
                <p><strong>Port:</strong> {settings.API_PORT}</p>
                <p><strong>Peers:</strong> {settings.PEER_IPS}</p>
            </div>
            <div class="card">
                <h2>Actions</h2>
                <p><a href="/docs" target="_blank">View Swagger API API Docs</a></p>
                <button onclick="fetch('/api/election/start', {{method: 'POST'}}).then(r=>alert('Election triggered!'))">Manually Trigger Election</button>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
