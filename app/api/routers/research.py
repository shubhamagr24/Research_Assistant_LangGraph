from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List
from app.api.services.agent_service import agent_service_instance
from app.api.graph.schemas import StartResearchRequest, FeedbackRequest, Analyst, ReportResponse, StateResponse, AnalystResponse

router = APIRouter()

@router.post("/start", response_model=StateResponse) # Returns initial state/analysts
async def start_new_research(request: StartResearchRequest):
    try:
        result = await agent_service_instance.start_research(request.topic, request.max_analysts)
        # The result from start_research needs to align with StateResponse or a specific response model
        return StateResponse(
            thread_id=result["thread_id"],
            state={"analysts": result.get("analysts", [])}, # Simplified state for now
            next_action=result.get("next_action")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{thread_id}/feedback", response_model=StateResponse)
async def submit_feedback(thread_id: str, request: FeedbackRequest):
    try:
        result = await agent_service_instance.provide_feedback_or_continue(thread_id, request.human_analyst_feedback)
        
        response_data = {
            "thread_id": result["thread_id"],
            "state": { # Simplified state for response
                "analysts": result.get("analysts", []),
                "final_report": result.get("final_report")
            },
            "next_action": result.get("next_action")
        }
        # If complete, include the final report in the main part of the response for clarity
        if result.get("is_complete") and result.get("final_report"):
            response_data["state"]["final_report"] = result["final_report"]
            # Potentially use a different response model for completed state

        return StateResponse(**response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{thread_id}/state", response_model=StateResponse)
async def get_thread_state(thread_id: str):
    try:
        state_info = agent_service_instance.get_current_state_info(thread_id)
        if "error" in state_info:
            raise HTTPException(status_code=404, detail=state_info["error"])
        
        # Adapt state_info to StateResponse
        # state_info['values'] is the full graph state. We might want to be selective.
        return StateResponse(
            thread_id=state_info["thread_id"],
            state=state_info.get("values", {}), 
            next_action=state_info.get("next_action")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))