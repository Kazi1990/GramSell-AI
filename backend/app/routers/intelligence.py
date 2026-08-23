import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import AgentRequest
from ..services.agents import run_pipeline, run_pipeline_events

router = APIRouter()

@router.post("/run")
async def run_intelligence(payload: AgentRequest, db: Session = Depends(get_db)):
    try:
        result = await run_pipeline(db, payload.seller_id, payload.message)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return {"agents": result}

@router.post("/run/stream")
async def stream_intelligence(payload: AgentRequest, db: Session = Depends(get_db)):
    async def events():
        try:
            async for event in run_pipeline_events(db, payload.seller_id, payload.message):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Agent pipeline failed'})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
