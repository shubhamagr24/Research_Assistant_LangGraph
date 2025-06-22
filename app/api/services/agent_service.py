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
        config = self_get_thread_config(thread_id)
        
        initial_input = {
            "topic": topic, 
            "max_analysts": max_analysts,
            "human_analyst_feedback": None, # Start with no feedback
            # Initialize other ResearchGraphState fields if necessary, though graph should handle defaults
            "analysts": [], 
            "sections": [],
            "introduction": "",
            "content": "",
            "conclusion": "",
            "final_report": ""
        }
        
        # Stream until interrupt or completion
        # Since it interrupts, we expect the stream to yield values then stop.
        events = []
        async for event in self.graph.astream_events(initial_input, config, version="v2", output_keys=["analysts", "final_report"]):
            events.append(event)
            if event["event"] == "on_chat_model_stream" and event["name"] == "human_feedback_node": # Heuristic
                 # This might be too specific or might not always be the exact event name
                 # A better way is to check the state or graph.get_state(config).next
                 pass

        current_state = self.graph.get_state(config)
        
        response = {
            "thread_id": thread_id,
            "analysts": current_state.values.get("analysts", []),
            "next_action": list(current_state.next) if current_state.next else None,
            "is_complete": not current_state.next # If 'next' is empty, it might be at END
        }
        if response["is_complete"]:
             response["final_report"] = current_state.values.get("final_report")
        return response

    async def provide_feedback_or_continue(self, thread_id: str, human_feedback: Optional[str]) -> Dict[str, Any]:
        config = self._get_thread_config(thread_id)
        
        # Update the state with the feedback. The graph is interrupted at 'human_feedback_node'.
        # The 'human_analyst_feedback' will be read by the conditional edge.
        self.graph.update_state(config, {"human_analyst_feedback": human_feedback})

        # Continue streaming from the interrupt.
        # Pass None as input because the state is already updated.
        events = []
        final_report_value = None
        analysts_value = None

        async for event_chunk in self.graph.astream(None, config, stream_mode="values"):
            # event_chunk will be the full state dictionary at each step where a node returns
            # We are interested in the final state or key values when it completes or interrupts again
            if "final_report" in event_chunk and event_chunk["final_report"]:
                final_report_value = event_chunk["final_report"]
            if "analysts" in event_chunk and event_chunk["analysts"]:
                 analysts_value = event_chunk["analysts"] # If it regenerates analysts

        current_state = self.graph.get_state(config)
        
        response = {
            "thread_id": thread_id,
            "analysts": analysts_value if analysts_value else current_state.values.get("analysts", []),
            "next_action": list(current_state.next) if current_state.next else None,
            "is_complete": not current_state.next
        }

        if response["is_complete"]:
            response["final_report"] = final_report_value if final_report_value else current_state.values.get("final_report")
        
        return response

    def get_current_state_info(self, thread_id: str) -> Dict[str, Any]:
        config = self._get_thread_config(thread_id)
        try:
            state = self.graph.get_state(config)
            if not state:
                 return {"error": "Thread ID not found or no state available.", "thread_id": thread_id}
            return {
                "thread_id": thread_id,
                "values": dict(state.values), # Convert TypedDict to dict for easier serialization
                "next_action": list(state.next) if state.next else None,
                "is_complete": not state.next
            }
        except Exception as e:
            # Handle cases where thread_id might not exist in MemorySaver after a restart
            return {"error": str(e), "thread_id": thread_id, "message": "State for thread_id may not exist."}

agent_service_instance = AgentService()