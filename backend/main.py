from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
from typing import Any, Dict, List

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import RAG pipeline
from rag.pipeline import get_tax_answer

# Create FastAPI app
app = FastAPI()

# Request body model
class QueryRequest(BaseModel):
    question: str
    chat_history: list = []
    tax_context: Dict[str, Any] = {}

# Root endpoint
@app.get("/")
def home():
    return {"message": "AI Tax Advisor Backend Running"}

# Ask endpoint
@app.post("/ask")
def ask_question(request: QueryRequest):

    # Call RAG pipeline directly
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