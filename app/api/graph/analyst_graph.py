from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver # Or another checkpointer
from .schemas import GenerateAnalystsState
from .nodes import create_analysts, human_feedback_node, should_continue_analyst_generation

def get_analyst_generation_graph():
    builder = StateGraph(GenerateAnalystsState)
    builder.add_node("create_analysts", create_analysts)
    builder.add_node("human_feedback_node", human_feedback_node) # Using the renamed node

    builder.add_edge(START, "create_analysts")
    builder.add_edge("create_analysts", "human_feedback_node")
    
    # Conditional edge to loop or end based on feedback
    builder.add_conditional_edges(
        "human_feedback_node",
        should_continue_analyst_generation,
        {"create_analysts": "create_analysts", "END": END}
    )
    
    # Interrupt before human_feedback_node to allow external feedback
    # This graph will be compiled by the main research_graph or used standalone if needed
    # For now, let's assume it's a sub-component and the main graph handles interrupts.
    # If used standalone, compile with interrupt_before=['human_feedback_node']
    return builder 

# Example of how it might be compiled if used alone:
# memory = MemorySaver()
# analyst_graph = get_analyst_generation_graph().compile(checkpointer=memory, interrupt_before=['human_feedback_node'])