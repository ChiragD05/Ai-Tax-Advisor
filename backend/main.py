from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys
import os
from typing import Any, Dict, List

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.pipeline import get_tax_answer

app = FastAPI()

# Allow Streamlit frontend to call FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    chat_history: List[dict] = Field(default_factory=list)
    tax_context: Dict[str, Any] = Field(default_factory=dict)

@app.get("/")
def home():
    return {"message": "AI Tax Advisor Backend Running"}

@app.post("/ask")
def ask_question(request: QueryRequest):
    answer, sources = get_tax_answer(
        request.question,
        request.chat_history,
        request.tax_context
    )

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources
    }