from fastapi import FastAPI
from app.api.routers import research
from app.api.core.config import OPENAI_API_KEY, TAVILY_API_KEY # To ensure they are loaded/checked

app = FastAPI(title="AI Research Assistant API")

# Simple check to ensure API keys are loaded (optional, config.py already raises error)
if not OPENAI_API_KEY or not TAVILY_API_KEY:
    print("WARNING: API keys might not be configured properly.")

app.include_router(research.router, prefix="/research", tags=["research"])

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Research Assistant API"}

# For development: allow all origins for CORS if Streamlit is on a different port
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify http://localhost:8501 for Streamlit dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)