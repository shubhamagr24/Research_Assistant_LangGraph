import uuid
from typing import Optional, Dict, Any, List
from app.api.graph.research_graph import main_research_graph
from app.api.graph.schemas import Analyst # For typing

class AgentService:
    def __init__(self):
        self.graph = main_research_graph

    def _get_thread_config(self, thread_id: str) -> Dict[str, Dict[str, str]]:
        return {"configurable": {"thread_id": thread_id}}

    async def start_research(self, topic: str, max_analysts: int) -> Dict[str, Any]:
        thread_id = str(uuid.uuid4())
        config = self._get_thread_config(thread_id)

        initial_input = {
            "topic": topic,
            "max_analysts": max_analysts,
            "human_analyst_feedback": None,
            "analysts": [],
            "sections": [],
            "introduction": "",
            "content": "",
            "conclusion": "",
            "final_report": ""
        }

        # Use ainvoke to run until the first interrupt or completion
        # ainvoke will return the final state of the graph run (or state at interrupt)
        await self.graph.ainvoke(initial_input, config)
        # After ainvoke, the checkpointer (MemorySaver) is updated.

        current_state = self.graph.get_state(config)
        if not current_state:
            raise Exception(f"Failed to get state for thread_id: {thread_id} after initial invoke.")

        response = {
            "thread_id": thread_id,
            "analysts": current_state.values.get("analysts", []),
            "next_action": list(current_state.next) if current_state.next else None,
            "is_complete": not current_state.next
        }
        return response

    async def provide_feedback_or_continue(self, thread_id: str, human_feedback: Optional[str]) -> Dict[str, Any]:
        config = self._get_thread_config(thread_id)

        self.graph.update_state(
            config,
            {"human_analyst_feedback": human_feedback}
        )

        # Continue execution using ainvoke from the updated state
        # Pass None as input to continue from the current state
        await self.graph.ainvoke(None, config)

        current_state = self.graph.get_state(config)
        if not current_state:
            raise Exception(f"Failed to get state for thread_id: {thread_id} after feedback invoke.")

        response = {
            "thread_id": thread_id,
            "analysts": current_state.values.get("analysts", []),
            "next_action": list(current_state.next) if current_state.next else None,
            "final_report": current_state.values.get("final_report") if not current_state.next else None,
            "is_complete": not current_state.next
        }
        return response

    def get_current_state_info(self, thread_id: str) -> Dict[str, Any]:
        config = self._get_thread_config(thread_id)
        try:
            state = self.graph.get_state(config)
            if not state:
                return {"error": "Thread ID not found or no state available.", "thread_id": thread_id}
            return {
                "thread_id": thread_id,
                "values": dict(state.values),
                "next_action": list(state.next) if state.next else None,
                "is_complete": not state.next
            }
        except Exception as e:
            return {"error": str(e), "thread_id": thread_id, "message": "State for thread_id may not exist."}

agent_service_instance = AgentService()