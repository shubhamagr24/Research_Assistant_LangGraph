# AI Research Assistant

This repository implements an **AI Research Assistant** using LangGraph for agentic workflows, FastAPI for the backend API, and Streamlit for the frontend user interface. The application is containerized using Docker for easy deployment.

## Features

- **Frontend**: A user-friendly interface built with Streamlit.
- **Backend**: A FastAPI-based API for managing research workflows.
- **LangGraph Integration**: Utilizes LangGraph for structured workflows and state management.
- **Parallel Processing**: Supports parallel interviews and report generation.
- **Customizable**: Easily extendable for new workflows or integrations.
- **Dockerized**: Fully containerized for seamless deployment.

---

## Project Structure

```plaintext
.
├── app/
│   ├── api/                # FastAPI backend logic
│   │   ├── core/           # Configuration and shared utilities
│   │   ├── graph/          # LangGraph workflows and nodes
│   │   ├── routers/        # API routes
│   │   ├── services/       # Service layer for business logic
│   │   ├── __init__.py
│   │   └── main.py         # FastAPI entry point
│   ├── frontend/           # Streamlit frontend logic
│   │   ├── app.py          # Streamlit app
│   │   └── __init__.py
├── experiments/            # Jupyter notebooks for testing and prototyping
├── Dockerfile.api          # Dockerfile for the FastAPI backend
├── Dockerfile.frontend     # Dockerfile for the Streamlit frontend
├── docker-compose.yml      # Docker Compose configuration
├── requirements_api.txt    # Backend dependencies
├── requirements_frontend.txt # Frontend dependencies
├── requirements.txt        # Combined dependencies
├── .env                    # Environment variables
├── README.md               # Project documentation
└── LICENSE                 # License file
```

---

## Prerequisites

- **Docker** and **Docker Compose** (for containerized deployment)
- **Python 3.9+** (for local development)
- API keys for:
  - **OpenAI** (for LLM integration)
  - **Tavily Search** (for search functionality)

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-research-assistant.git
cd ai-research-assistant
```

### 2. Configure Environment Variables
Create a `.env` file in the project root (or copy the example):
```bash
cp .env.example .env
```
Update the `.env` file with your API keys:
```env
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

### 3. Build and Run with Docker Compose
```bash
docker-compose up --build
```
- The **backend** will be available at `http://localhost:8000`.
- The **frontend** will be available at `http://localhost:8501`.

---

## Local Development (Without Docker)

### 1. Install Dependencies
Install Python dependencies for both the backend and frontend:
```bash
pip install -r requirements.txt
```

### 2. Run the Backend
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run the Frontend
Update the `FASTAPI_URL` in `app/frontend/app.py` to:
```python
FASTAPI_URL = "http://localhost:8000/research"
```
Then, start the Streamlit app:
```bash
streamlit run app/frontend/app.py
```

---

## Usage

1. Open the frontend in your browser at `http://localhost:8501`.
2. Enter a research topic and the number of analysts to generate.
3. Interact with the generated analysts, provide feedback, and generate a final research report.

---

## API Endpoints

### Base URL
`http://localhost:8000/research`

### Endpoints
- **POST /start**: Start a new research session.
- **POST /{thread_id}/feedback**: Submit feedback or continue the research process.
- **GET /{thread_id}/state**: Retrieve the current state of a research session.

---

## Technologies Used

- **LangGraph**: For structured workflows and state management.
- **FastAPI**: Backend API framework.
- **Streamlit**: Frontend framework for interactive UI.
- **Docker**: Containerization for deployment.
- **OpenAI API**: For LLM-based interactions.
- **Tavily Search API**: For search and retrieval.

---

## Development Notes

- **Live Reload**: Docker Compose mounts the `app/` directory for live code updates during development.
- **Testing**: Use the `experiments/` directory for prototyping and testing workflows with Jupyter notebooks.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

## Acknowledgments

- [LangGraph](https://github.com/langgraph) for enabling structured workflows.
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework.
- [Streamlit](https://streamlit.io/) for the frontend framework.