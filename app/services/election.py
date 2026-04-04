import asyncio
import httpx
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.domain import ElectionState
from app.core.config import settings
import datetime

# Priority calculation for Bully Algorithm
# Here we'll just use the node_id string comparison as priority, where 'node3' > 'node2' > 'node1'
# You can customize it to be based on IP or a specific rank integer

async def start_election():
    """
    Bully Algorithm:
    1. Node broadcasts ELECTION message to all nodes with HIGHER priority.
    2. If no one answers, it declares itself LEADER and broadcasts VICTORY.
    3. If someone answers, it steps down and waits for VICTORY message.
    """
    print(f"Node {settings.NODE_ID} starting Election...")
    peers = [p.strip() for p in settings.PEER_IPS.split(",") if p.strip()]
    
    higher_peers = []
    # Assuming NODE_ID format is 'node1', 'node2', etc., we can do string comparison
    for peer in peers:
        # In a real scenario, we'd query the peer's actual ID. 
        # For this prototype, we assume peer format or simply ping all and let them decide.
        # To simplify, we ping ALL active peers and send our node_id.
        pass
        
    # Standard Bully
    db = SessionLocal()
    # Ensure current election state
    state = db.query(ElectionState).filter_by(node_id=settings.NODE_ID).first()
    if not state:
        state = ElectionState(node_id=settings.NODE_ID, current_term=1, state="CANDIDATE")
        db.add(state)
    else:
        state.state = "CANDIDATE"
        state.current_term += 1
    db.commit()
    
    # Send ELECTION call to all peers
    won_election = True
    async with httpx.AsyncClient() as client:
        for peer in peers:
            try:
                url = f"http://{peer}/api/election/ping"
                params = {"candidate_id": settings.NODE_ID}
                resp = await client.post(url, params=params, timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    # If peer says "I yield", we keep winning
                    # If peer says "I am higher", we lose.
                    if data.get("action") == "yield":
                        continue
                    elif data.get("action") == "reject":
                        won_election = False
                        break
            except Exception:
                pass # Peer is likely dead
                
    if won_election:
        print(f"Node {settings.NODE_ID} won the election!")
        state.state = "LEADER"
        state.leader_id = settings.NODE_ID
        db.commit()
        # Broadcast VICTORY
        async with httpx.AsyncClient() as client:
            for peer in peers:
                url = f"http://{peer}/api/election/victory"
                await client.post(url, params={"leader_id": settings.NODE_ID}, timeout=2.0)
    else:
        print(f"Node {settings.NODE_ID} stepped down, waiting for new leader.")
        state.state = "FOLLOWER"
        db.commit()
    db.close()
