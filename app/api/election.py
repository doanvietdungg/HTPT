from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.domain import ElectionState
from app.core.config import settings
from app.services.election import start_election

router = APIRouter()

@router.post("/ping")
def election_ping(candidate_id: str, db: Session = Depends(get_db)):
    """
    Called by a Candidate starting an election.
    """
    # Simple Priority: String comparison of NODE_ID. 'node3' > 'node2'
    if settings.NODE_ID > candidate_id:
        return {"action": "reject"} # I have a higher priority, you cannot be leader
    else:
        return {"action": "yield"} # I have lower priority, you can be leader

@router.post("/victory")
def election_victory(leader_id: str, db: Session = Depends(get_db)):
    """
    Called by the winner of the election to assert dominance.
    """
    state = db.query(ElectionState).filter_by(node_id=settings.NODE_ID).first()
    if not state:
        state = ElectionState(node_id=settings.NODE_ID, state="FOLLOWER")
        db.add(state)
        
    state.leader_id = leader_id
    state.state = "FOLLOWER"
    db.commit()
    print(f"Acknowledged Node {leader_id} as the new Leader.")
    return {"status": "ok"}

@router.post("/start")
def trigger_election_manually(background_tasks: BackgroundTasks):
    """
    Manually trigger an election (e.g. if heartbeat failure detects Leader is down)
    """
    background_tasks.add_task(start_election)
    return {"status": "election_started"}
