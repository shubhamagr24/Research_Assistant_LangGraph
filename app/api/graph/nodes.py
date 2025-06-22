from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain.document_loaders import WikipediaLoader
from .schemas import GenerateAnalystsState, Perspectives, InterviewState, SearchQuery, Analyst, ResearchGraphState
from app.api.core.config import (
    llm, tavily_search,max_interview_turns,
    analyst_instructions_template, question_instructions_template,
    search_instructions_content, answer_instructions_template,
    section_writer_instructions_template, report_writer_instructions_template,
    intro_conclusion_instructions_template
)


def create_analysts(state: GenerateAnalystsState) -> dict:
    system_prompt = analyst_instructions_template.format(
        topic=state['topic'],
        human_analyst_feedback=state.get('human_analyst_feedback', ''),
        max_analysts=state['max_analysts']
    )
    structured_llm = llm.with_structured_output(Perspectives)
    response = structured_llm.invoke([SystemMessage(content=system_prompt)] + [HumanMessage(content="Generate the set of analysts.")])
    return {'analysts': response.analysts, 'human_analyst_feedback': state.get('human_analyst_feedback', None)} # pass feedback along

def human_feedback_node(state: GenerateAnalystsState) -> dict: 
    """Dummy no-op node, state passes through."""
    return {} # No changes to state from this node itself

def should_continue_analyst_generation(state: GenerateAnalystsState) -> str:
    if state.get('human_analyst_feedback', None):
        # If human feedback is provided, we want to regenerate analysts
        return "create_analysts"
    return "END"


# --- Interview Graph Nodes 
def generate_question(state: InterviewState) -> dict:
    system_prompt = question_instructions_template.format(goals=state['analyst'].persona)
    response = llm.invoke([SystemMessage(content=system_prompt)] + state['messages'])
    return {'messages': [response]} # Append new message

def create_search_query(state: InterviewState) -> dict:
    search_sys_message = SystemMessage(content=search_instructions_content)
    llm_with_structured_output = llm.with_structured_output(SearchQuery)
    response = llm_with_structured_output.invoke([search_sys_message] + state['messages'])
    return {'search_query': response.search_query}

def web_search(state: InterviewState) -> dict:
    search_query = state['search_query']
    search_docs_raw = tavily_search.invoke(search_query)
    formatted_search_docs = "\n\n---\n\n".join(
        [f'<Document href="{doc["url"]}" />\n{doc["content"]}\n</Document>' for doc in search_docs_raw]
    )
    return {"context": [formatted_search_docs]}

def search_wikipedia(state: InterviewState) -> dict:
    search_query = state['search_query']
    loader = WikipediaLoader(query=search_query, load_max_docs=3) 
    docs = loader.load()
    formatted_search_docs = "\n\n---\n\n".join(
        [f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}" />\n{doc.page_content}\n</Document>' for doc in docs]
    )
    return {"context": [formatted_search_docs]}
    
def generate_answer(state: InterviewState) -> dict:
    analyst = state["analyst"]
    messages = state["messages"]
    context = state["context"] # This should be a string by now
    
    # Ensure context is a single string
    full_context_str = "\n\n".join(context) if isinstance(context, list) else context

    system_message_content = answer_instructions_template.format(goals=analyst.persona, context=full_context_str)
    answer = llm.invoke([SystemMessage(content=system_message_content)] + messages)
    answer.name = "expert"
    return {"messages": [answer]}

def save_interview(state: InterviewState) -> dict:
    messages = state["messages"]
    interview_str = get_buffer_string(messages)
    return {"interview": interview_str}

def route_messages(state: InterviewState, name: str = "expert") -> str:
    messages = state["messages"]
    max_num_turns = state.get('max_num_turns', max_interview_turns)
    num_responses = len([m for m in messages if isinstance(m, AIMessage) and m.name == name])

    if num_responses >= max_num_turns:
        return 'save_interview'
    
    # Check last *analyst* question (which would be messages[-2] if expert just answered)
    # The router runs after generate_answer, so messages[-1] is expert's answer, messages[-2] is analyst's question
    if len(messages) >= 2:
        last_question = messages[-2]
        if isinstance(last_question, HumanMessage) or (isinstance(last_question, AIMessage) and last_question.name != "expert"): # Analyst question
             if "Thank you so much for your help" in last_question.content:
                return 'save_interview'
    return "ask_question"

def write_section(state: InterviewState) -> dict:
    interview = state["interview"]
    context = state["context"] # Context used for RAG
    analyst = state["analyst"]
    
    full_context_str = "\n\n".join(context) if isinstance(context, list) else context

    system_message_content = section_writer_instructions_template.format(focus=analyst.description)
    section = llm.invoke([
        SystemMessage(content=system_message_content),
        HumanMessage(content=f"Use these sources: {full_context_str}\n\nAnd this expert interview: {interview}")
    ])
    return {"sections": [section.content]} # This will be aggregated by operator.add



from langgraph.constants import Send # For initiate_all_interviews

def initiate_all_interviews_conditional(state: ResearchGraphState): # This is the conditional_edge function
    human_analyst_feedback = state.get('human_analyst_feedback')
    if human_analyst_feedback:
        return "create_analysts"  # Go back to regenerate analysts
    else:
        # Proceed to conduct interviews in parallel
        topic = state["topic"]
        return [
            Send(
                "conduct_interview",
                {
                    "analyst": analyst,
                    "messages": [HumanMessage(content=f"So you said you were writing an article on {topic}?")],
                    "max_num_turns": state.get("max_num_turns_interview", max_interview_turns), # Allow configuring interview turns
                    "context": [], # Initialize context for interview
                    "sections": [] # Initialize sections for interview
                }
            ) for analyst in state["analysts"]
        ]

def write_report(state: ResearchGraphState) -> dict:
    sections = state["sections"]
    topic = state["topic"]
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    system_message_content = report_writer_instructions_template.format(topic=topic, context=formatted_str_sections)
    report = llm.invoke([SystemMessage(content=system_message_content)] + [HumanMessage(content="Write a report based upon these memos.")])
    return {"content": report.content}

def write_introduction(state: ResearchGraphState) -> dict:
    sections = state["sections"]
    topic = state["topic"]
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    instructions = intro_conclusion_instructions_template.format(topic=topic, formatted_str_sections=formatted_str_sections)
    intro = llm.invoke([SystemMessage(content=instructions)] + [HumanMessage(content="Write the report introduction")])
    return {"introduction": intro.content}

def write_conclusion(state: ResearchGraphState) -> dict:
    sections = state["sections"]
    topic = state["topic"]
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    instructions = intro_conclusion_instructions_template.format(topic=topic, formatted_str_sections=formatted_str_sections)
    conclusion = llm.invoke([SystemMessage(content=instructions)] + [HumanMessage(content="Write the report conclusion")])
    return {"conclusion": conclusion.content}

def finalize_report(state: ResearchGraphState) -> dict:
    content = state["content"]
    # Parsing logic from notebook
    if content.startswith("## Insights"): # Ensure it's ## Insights as per prompt
        # Find the start of "## Insights" and take everything after it.
        # This handles cases where there might be leading whitespace or other text if LLM is not perfectly compliant.
        insights_marker = "## Insights"
        insights_start_index = content.find(insights_marker)
        if insights_start_index != -1:
            content_body = content[insights_start_index + len(insights_marker):].strip()
        else: # Fallback if marker not found
            content_body = content 

    sources_marker = "\n## Sources\n" # More robust split
    if sources_marker in content_body:
        try:
            # Split based on the last occurrence of sources_marker to be safe
            parts = content_body.rsplit(sources_marker, 1)
            content_main = parts[0]
            sources_text = parts[1] if len(parts) > 1 else None
        except Exception:
            content_main = content_body # Fallback
            sources_text = None
    else:
        content_main = content_body
        sources_text = None
    
    final_report_parts = [state["introduction"]]
    if content_main: # Add content if it exists
      final_report_parts.append(content_main)
    final_report_parts.append(state["conclusion"])

    final_report_str = "\n\n---\n\n".join(filter(None, final_report_parts)) # Filter out potential None/empty strings
    
    if sources_text:
        final_report_str += "\n\n## Sources\n" + sources_text.strip()
        
    return {"final_report": final_report_str.strip()}