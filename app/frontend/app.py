import streamlit as st
import requests # To call FastAPI
import time # For simulated progress

FASTAPI_URL = "http://api:8000/research" # Ensure this is correct for Docker Compose
# FASTAPI_URL = "http://localhost:8000/research" # For local dev

st.set_page_config(layout="wide")
st.title("📝 AI Research Assistant")

# Initialize session state variables
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "analysts" not in st.session_state:
    st.session_state.analysts = []
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "current_step" not in st.session_state:
    st.session_state.current_step = "initial_input" # initial_input, show_analysts, show_report
if "processing" not in st.session_state: # for loading indicators
    st.session_state.processing = False


def display_analysts(analysts_list):
    if analysts_list:
        st.subheader("Generated Analysts:")
        for i, analyst in enumerate(analysts_list):
            # Ensure analyst is a dict if it comes from JSON
            analyst_data = analyst if isinstance(analyst, dict) else analyst.model_dump() if hasattr(analyst, 'model_dump') else {}

            with st.expander(f"Analyst {i+1}: {analyst_data.get('name', 'N/A')}", expanded=i==0):
                st.markdown(f"**Name:** {analyst_data.get('name', 'N/A')}")
                st.markdown(f"**Affiliation:** {analyst_data.get('affiliation', 'N/A')}")
                st.markdown(f"**Role:** {analyst_data.get('role', 'N/A')}")
                st.markdown(f"**Description:** {analyst_data.get('description', 'N/A')}")
                st.markdown(f"**Question Style:** {analyst_data.get('question_style', 'N/A')}")
    else:
        st.info("No analysts generated yet or an issue occurred.")

# --- UI Sections ---

# Step 1: Initial Input
if st.session_state.current_step == "initial_input":
    with st.form("research_form"):
        topic = st.text_input("Research Topic:", placeholder="e.g., The future of AI in healthcare")
        max_analysts = st.number_input("Number of Analysts to Generate:", min_value=1, max_value=5, value=3)
        submit_button = st.form_submit_button("Start Research")

    if submit_button and topic:
        st.session_state.processing = True
        st.session_state.error_message = None
        st.session_state.final_report = None # Reset previous report
        st.session_state.analysts = [] # Reset analysts
        with st.spinner("Initializing research and generating analysts... This may take a moment."):
            try:
                response = requests.post(f"{FASTAPI_URL}/start", json={"topic": topic, "max_analysts": max_analysts})
                response.raise_for_status()
                data = response.json()
                st.session_state.thread_id = data.get("thread_id")
                state_data = data.get("state", {})
                st.session_state.analysts = state_data.get("analysts", [])

                if st.session_state.analysts:
                    st.session_state.current_step = "show_analysts"
                else:
                    st.session_state.error_message = "No analysts were generated. Please check the topic or backend logs."
                
            except requests.exceptions.RequestException as e:
                st.session_state.error_message = f"API Error: {e}. Is the backend running at {FASTAPI_URL}?"
            except Exception as e:
                st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
        st.session_state.processing = False
        st.rerun() # MODIFIED HERE

# Step 2: Show Analysts and Get Feedback
elif st.session_state.current_step == "show_analysts" and st.session_state.thread_id:
    display_analysts(st.session_state.analysts)
    
    st.subheader("Provide Feedback (Optional)")
    feedback = st.text_area("Your feedback on the generated analysts:", 
                            placeholder="e.g., Focus more on financial implications.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate Analysts with Feedback", disabled=st.session_state.processing or not feedback.strip()): # Check if feedback is not just whitespace
            st.session_state.processing = True
            st.session_state.error_message = None
            with st.spinner("Regenerating analysts based on your feedback..."):
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/{st.session_state.thread_id}/feedback",
                        json={"human_analyst_feedback": feedback}
                    )
                    response.raise_for_status()
                    data = response.json()
                    state_data = data.get("state", {})
                    st.session_state.analysts = state_data.get("analysts", []) 
                    if not state_data.get("final_report"): # If still in analyst feedback loop
                         pass # Rerun will happen at the end of this block
                    else: 
                         st.session_state.error_message = "Unexpected completion after feedback for regeneration."
                         st.session_state.final_report = state_data.get("final_report")
                         st.session_state.current_step = "show_report"


                except requests.exceptions.RequestException as e:
                    st.session_state.error_message = f"API Error: {e}"
                except Exception as e:
                    st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
            st.session_state.processing = False
            st.rerun() # MODIFIED HERE


    with col2:
        if st.button("✅ Proceed & Generate Full Report", disabled=st.session_state.processing):
            st.session_state.processing = True
            st.session_state.error_message = None
            with st.spinner("Analysts confirmed. Generating the full research report... This will take several minutes."):
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/{st.session_state.thread_id}/feedback",
                        json={"human_analyst_feedback": None} 
                    )
                    response.raise_for_status()
                    data = response.json()
                    state_data = data.get("state", {})
                    st.session_state.final_report = state_data.get("final_report")
                    if st.session_state.final_report:
                        st.session_state.current_step = "show_report"
                    else: # If it's not complete, it might have new analysts or an error
                        st.session_state.analysts = state_data.get("analysts", [])
                        if not st.session_state.analysts: # If no analysts and no report, something is wrong
                            st.session_state.error_message = "Report generation did not complete and no analysts returned. Check backend logs."
                        # If analysts are returned, it stays in 'show_analysts' implicitly by not changing current_step
                        # This covers the case where the graph logic might loop back to analyst generation.

                except requests.exceptions.RequestException as e:
                    st.session_state.error_message = f"API Error: {e}"
                except Exception as e:
                    st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
            st.session_state.processing = False
            st.rerun() # MODIFIED HERE

# Step 3: Show Final Report
elif st.session_state.current_step == "show_report" and st.session_state.final_report:
    st.subheader("Generated Research Report")
    st.markdown(st.session_state.final_report)
    if st.button("Start New Research"):
        # Reset state for a new research task
        st.session_state.thread_id = None
        st.session_state.analysts = []
        st.session_state.final_report = None
        st.session_state.error_message = None
        st.session_state.current_step = "initial_input"
        st.rerun() # MODIFIED HERE

# Display error messages if any
if st.session_state.error_message:
    st.error(st.session_state.error_message)

# Footer or debug info (optional)
if st.session_state.thread_id:
    st.sidebar.markdown(f"**Current Thread ID:** `{st.session_state.thread_id}`")
    if st.sidebar.button("Refresh Current State from API (Debug)"):
        if st.session_state.thread_id:
            try:
                res = requests.get(f"{FASTAPI_URL}/{st.session_state.thread_id}/state")
                res.raise_for_status()
                st.sidebar.json(res.json())
            except Exception as e:
                st.sidebar.error(f"Failed to fetch state: {e}")
        else:
            st.sidebar.info("No active thread ID.")