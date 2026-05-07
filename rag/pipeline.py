from dotenv import load_dotenv
import os
from datetime import datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from utils.web_search import duckduckgo_search

load_dotenv()

# Embeddings
embeddings = OpenAIEmbeddings()

# Load FAISS once at startup
db = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# LLM
llm = ChatOpenAI(
    model="gpt-5.5",
    temperature=0
)


def needs_web_search(query: str) -> bool:
    keywords = [
        "latest",
        "current",
        "today",
        "2025",
        "2026",
        "budget",
        "new tax",
        "tax update",
        "recent",
        "government",
        "cbdt",
        "news",
        "deadline",
        "notification",
        "revenue",
        "slab",
        "rebate"
    ]

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in keywords)


def get_tax_answer(query, chat_history=None, tax_context=None):
    chat_history = chat_history or []
    tax_context = tax_context or {}

    current_datetime = datetime.now().strftime("%d %B %Y, %I:%M %p")
    # Load the correct vector DB for this chat/session
    vectorstore_path = tax_context.get("vectorstore_path")

    if vectorstore_path and os.path.exists(vectorstore_path):
        active_db = FAISS.load_local(
            vectorstore_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        active_db = FAISS.load_local(
            "faiss_index",
            embeddings,
            allow_dangerous_deserialization=True
        )
    # Internal RAG search
    docs = db.similarity_search(query, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # Conversation history
    history = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in chat_history
    )

    # Live web search context
    web_context = ""
    if needs_web_search(query):
        web_results = duckduckgo_search(query)

        web_context = "\n\n".join([
            f"""
Title: {r['title']}
Content: {r['body']}
Source: {r['link']}
"""
            for r in web_results
        ])

    # Tax profile context
    tax_profile = ""
    if tax_context:
        tax_profile = f"""
CURRENT USER TAX PROFILE:

Salary: ₹{tax_context.get('salary', 0):,.0f}
Current Tax Regime: {tax_context.get('regime', '')}
Total Selected Deductions: ₹{tax_context.get('selected_total', 0):,.0f}
Deduction Breakdown: {tax_context.get('deduction_breakdown', {})}
Calculated Old Regime Tax: ₹{tax_context.get('old_tax', 0):,.2f}
Calculated New Regime Tax: ₹{tax_context.get('new_tax', 0):,.2f}
Best Regime: {tax_context.get('best_regime', '')}

IMPORTANT:
- Use these tax values directly.
- Do not assume taxable income.
- Do not invent salary numbers.
- Do not create hypothetical examples unless user asks.
"""

    # Final prompt
    prompt = f"""
You are an expert Indian tax advisor.

Current Date & Time:
{current_datetime}

You help users understand:
- deductions
- HRA
- 80C
- old vs new regime
- tax planning
- tax optimization

Use the user's ACTUAL calculated tax profile below.

{tax_profile}

Previous Conversation:
{history}

Relevant Tax Knowledge:
{context}

Live Web Search Results:
{web_context}

User Question:
{query}

Instructions:
- Use the exact calculated values from the tax profile.
- Never assume salary or taxable income.
- Never create hypothetical examples unless asked.
- If live web results are available, use them carefully.
- Prefer official/current information when available.
- Answer specifically for THIS user.
- Keep answers practical and conversational.

Answer:
"""

    response = llm.invoke(prompt)

    sources = [doc.page_content[:200] for doc in docs]
    return response.content, sources