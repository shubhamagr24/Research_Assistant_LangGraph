import streamlit as st
import requests # To call FastAPI
import time # For simulated progress

FASTAPI_URL = "http://localhost:8000/research" # Change to 'http://api:8000/research' in Docker Compose

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
            with st.expander(f"Analyst {i+1}: {analyst.get('name', 'N/A')}", expanded=i==0):
                st.markdown(f"**Name:** {analyst.get('name', 'N/A')}")
                st.markdown(f"**Affiliation:** {analyst.get('affiliation', 'N/A')}")
                st.markdown(f"**Role:** {analyst.get('role', 'N/A')}")
                st.markdown(f"**Description:** {analyst.get('description', 'N/A')}")
                st.markdown(f"**Question Style:** {analyst.get('question_style', 'N/A')}")
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
                # The 'analysts' might be nested inside 'state' based on StateResponse
                state_data = data.get("state", {})
                st.session_state.analysts = state_data.get("analysts", [])

                if st.session_state.analysts:
                    st.session_state.current_step = "show_analysts"
                else: # Should not happen if API works correctly, but handle
                    st.session_state.error_message = "No analysts were generated. Please check the topic."
                
            except requests.exceptions.RequestException as e:
                st.session_state.error_message = f"API Error: {e}. Is the backend running?"
            except Exception as e:
                st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
        st.session_state.processing = False
        st.experimental_rerun() # Rerun to reflect state change

# Step 2: Show Analysts and Get Feedback
elif st.session_state.current_step == "show_analysts" and st.session_state.thread_id:
    display_analysts(st.session_state.analysts)
    
    st.subheader("Provide Feedback (Optional)")
    feedback = st.text_area("Your feedback on the generated analysts:", 
                            placeholder="e.g., Focus more on financial implications.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate Analysts with Feedback", disabled=st.session_state.processing or not feedback):
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
                    st.session_state.analysts = state_data.get("analysts", []) # Update analysts
                    # If regeneration still leads to 'show_analysts' (i.e., not complete)
                    if not data.get("state",{}).get("final_report"):
                         st.experimental_rerun() # Rerun to display new analysts
                    else: # Should not happen here, feedback implies another analyst round
                         st.session_state.error_message = "Unexpected completion after feedback for regeneration."

                except requests.exceptions.RequestException as e:
                    st.session_state.error_message = f"API Error: {e}"
                except Exception as e:
                    st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
            st.session_state.processing = False
            st.experimental_rerun()


    with col2:
        if st.button("✅ Proceed & Generate Full Report", disabled=st.session_state.processing):
            st.session_state.processing = True
            st.session_state.error_message = None
            with st.spinner("Analysts confirmed. Generating the full research report... This will take several minutes."):
                try:
                    # Send None or empty feedback to proceed
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
                    else:
                        st.session_state.error_message = "Report generation did not complete as expected. Check backend logs."
                        # Potentially it could go back to analyst generation if something is misconfigured
                        st.session_state.analysts = state_data.get("analysts", [])
                        if st.session_state.analysts and not st.session_state.final_report:
                            st.session_state.current_step = "show_analysts" # Stay here if it loops back

                except requests.exceptions.RequestException as e:
                    st.session_state.error_message = f"API Error: {e}"
                except Exception as e:
                    st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
            st.session_state.processing = False
            st.experimental_rerun()

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
        st.experimental_rerun()

# Display error messages if any
if st.session_state.error_message:
    st.error(st.session_state.error_message)

# Footer or debug info (optional)
# st.sidebar.json(st.session_state)
if st.session_state.thread_id:
    st.sidebar.markdown(f"**Current Thread ID:** `{st.session_state.thread_id}`")
    if st.sidebar.button("Refresh Current State from API (Debug)"):
        try:
            res = requests.get(f"{FASTAPI_URL}/{st.session_state.thread_id}/state")
            res.raise_for_status()
            st.sidebar.json(res.json())
        except Exception as e:
            st.sidebar.error(f"Failed to fetch state: {e}")