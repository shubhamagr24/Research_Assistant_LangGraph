from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .schemas import ResearchGraphState
from .nodes import (
    create_analysts, human_feedback_node, # from analyst generation logic
    initiate_all_interviews_conditional,  # conditional edge logic
    write_report, write_introduction, write_conclusion, finalize_report
)
from .interview_graph import get_interview_graph_builder # To compile the interview sub-graph

def get_research_graph():
    # Compile the interview graph first as it's a node in the research graph
    # No separate checkpointer for subgraphs usually, main graph checkpointer manages all.
    compiled_interview_graph = get_interview_graph_builder().compile()

    builder = StateGraph(ResearchGraphState)

    # Nodes from analyst generation cycle + main research tasks
    builder.add_node("create_analysts", create_analysts) 
    builder.add_node("human_feedback_node", human_feedback_node) 
    
    # The interview graph is a node that processes one interview
    # The `initiate_all_interviews_conditional` will use Send to invoke it multiple times
    builder.add_node("conduct_interview", compiled_interview_graph)
    
    builder.add_node("write_report", write_report)
    builder.add_node("write_introduction", write_introduction)
    builder.add_node("write_conclusion", write_conclusion)
    builder.add_node("finalize_report", finalize_report)

    builder.add_edge(START, "create_analysts")
    builder.add_edge("create_analysts", "human_feedback_node") # This is the interrupt point

    # Conditional branching after feedback (or no feedback)
    builder.add_conditional_edges(
        "human_feedback_node",
        initiate_all_interviews_conditional, # This function returns node name or Send list
        {
            "create_analysts": "create_analysts", # Path if feedback leads to re-creation
            "conduct_interview": "conduct_interview" # Path if Send invokes conduct_interview
        }
    )
    
    # After all parallel interviews are done and sections are aggregated:
    # These three can run in parallel after 'conduct_interview' finishes for all analysts
    # LangGraph handles this: if a node has multiple outgoing edges not conditional,
    # and subsequent nodes don't depend on each other, they might run in parallel.


 

    # The conduct_interview node will aggregate sections into the state
    builder.add_edge("conduct_interview", "write_report")
    builder.add_edge("conduct_interview", "write_introduction")
    builder.add_edge("conduct_interview", "write_conclusion")
    
    # This join ensures finalize_report runs after all three are done.
    builder.add_edge(["write_report", "write_introduction", "write_conclusion"], "finalize_report")

    builder.add_edge("finalize_report", END)
    
    memory = MemorySaver()
    # The main graph is compiled with the interrupt point
    research_graph_compiled = builder.compile(
        checkpointer=memory, 
        interrupt_before=['human_feedback_node']
    )
    return research_graph_compiled

# Global instance of the compiled graph
main_research_graph = get_research_graph()