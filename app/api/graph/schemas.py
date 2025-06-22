from pydantic import BaseModel, Field
from langgraph.graph import MessagesState
from typing import List, TypedDict, Optional
from typing import Annotated # Changed from typing import Annotated for older python versions if any issue
import operator # For Annotated with operator.add


class Analyst(BaseModel):
    affiliation: str = Field(description="Primary affiliation of the analyst.")
    name: str = Field(description="Name of the analyst.")
    role: str = Field(description="Role of the analyst in the context of the topic.")
    description: str = Field(description="Description of the analyst focus, concerns, and motives.")
    question_style: str = Field(description="How this analyst typically frames questions")
    
    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\nquestion_style: {self.question_style}"


class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(description="Comprehensive list of analysts with their roles and affiliations.")


class GenerateAnalystsState(TypedDict):
    topic: str
    max_analysts: int
    human_analyst_feedback: Optional[str] # Made optional as it's not always present
    analysts: List[Analyst]


class InterviewState(MessagesState): 
    max_num_turns: int
    context: Annotated[list, operator.add]
    search_query: str
    analyst: Analyst
    interview: str
    sections: Annotated[list, operator.add] # Final key we duplicate in outer state for Send() API


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Search query for retrieval.")


class ResearchGraphState(TypedDict):
    topic: str
    max_analysts: int
    human_analyst_feedback: Optional[str] # Made optional
    analysts: List[Analyst]
    sections: Annotated[list, operator.add]
    introduction: str
    content: str
    conclusion: str
    final_report: str

# API Request/Response Models (New for FastAPI)
class StartResearchRequest(BaseModel):
    topic: str
    max_analysts: int

class FeedbackRequest(BaseModel):
    human_analyst_feedback: Optional[str]

class AnalystResponse(BaseModel):
    analysts: List[Analyst]
    thread_id: str

class ReportResponse(BaseModel):
    final_report: str
    thread_id: str

class StateResponse(BaseModel):
    state: dict
    next_action: Optional[List[str]] = None # To guide the frontend
    thread_id: str