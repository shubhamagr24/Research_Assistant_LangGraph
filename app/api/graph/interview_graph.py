from langgraph.graph import StateGraph, START, END
from .schemas import InterviewState
from .nodes import (
    generate_question, create_search_query, web_search, search_wikipedia,
    generate_answer, save_interview, route_messages, write_section
)

def get_interview_graph_builder(): # Returns builder, compilation happens in research_graph
    interview_builder = StateGraph(InterviewState)
    interview_builder.add_node("ask_question", generate_question)
    interview_builder.add_node("create_search_query", create_search_query)
    interview_builder.add_node("web_search", web_search)
    interview_builder.add_node("search_wikipedia", search_wikipedia)
    interview_builder.add_node("generate_answer", generate_answer)
    interview_builder.add_node("save_interview", save_interview)
    interview_builder.add_node("write_section", write_section)

    interview_builder.add_edge(START, "ask_question")
    interview_builder.add_edge("ask_question", "create_search_query")
    
    # Parallel search paths - after create_search_query, both web_search and search_wikipedia can run
    # Then results are aggregated in context (Annotated[list, operator.add])
    # The graph implicitly handles this if they both update 'context' and 'generate_answer' reads it.
    interview_builder.add_edge("create_search_query", "web_search") 
    interview_builder.add_edge("create_search_query", "search_wikipedia") 

    interview_builder.add_edge("web_search", "generate_answer")
    interview_builder.add_edge("search_wikipedia", "generate_answer")
    
    interview_builder.add_conditional_edges(
        'generate_answer', 
        route_messages, 
        {"ask_question": "ask_question", "save_interview": "save_interview"}
    )
    interview_builder.add_edge("save_interview", "write_section")
    interview_builder.add_edge("write_section", END)
    
    return interview_builder

