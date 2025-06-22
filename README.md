# AI Research Assistant

This project implements an AI Research Assistant using LangGraph for agentic workflows, FastAPI for the backend API, and Streamlit for the frontend user interface. The entire application is containerized using Docker.

## Project Structure

ai_research_assistant/
├── app/
│ ├── api/ # FastAPI backend logic
│ └── frontend/ # Streamlit frontend logic
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements_api.txt
├── requirements_frontend.txt
├── .env.example # Example for environment variables
└── README.md


## Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development if not using Docker exclusively)
- An OpenAI API Key
- A Tavily Search API Key

## Setup

1.  **Clone the repository (if applicable) or create the files as described.**
2.  **Create Environment File:**
    Copy `.env.example` to a new file named `.env` in the project root:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and add your actual `OPENAI_API_KEY` and `TAVILY_API_KEY`.

3.  **Modify Frontend API URL (If running with Docker Compose):**
    In `app/frontend/app.py`, change the `FASTAPI_URL` to point to the API service name within the Docker network:
    ```python
    FASTAPI_URL = "http://api:8000/research" 
    ```
    (For local development where Streamlit runs outside Docker and FastAPI runs locally or in Docker mapped to localhost, use `http://localhost:8000/research`).

