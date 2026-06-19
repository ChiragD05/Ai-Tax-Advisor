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
    docs = active_db.similarity_search(query, k=3)
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
    form16_data = tax_context.get("form16_data", {})

    if form16_data:
      tax_profile += f"""
FORM 16 SUMMARY:
Employer Name: {form16_data.get('employer_name')}
Employee Name: {form16_data.get('employee_name')}
Gross Salary: ₹{form16_data.get('gross_salary') or 0:,.2f}
Exemptions: ₹{form16_data.get('exemptions') or 0:,.2f}
Deductions: ₹{form16_data.get('deductions') or 0:,.2f}
Taxable Income: ₹{form16_data.get('taxable_income') or 0:,.2f}
TDS: ₹{form16_data.get('tds') or 0:,.2f}

IMPORTANT:
Use the extracted Form 16 data directly.
Do not invent salary or taxable income values.
"""

    # Final prompt
    prompt = f"""
You are an elite, highly professional Indian Tax Advisor AI. Your primary objective is to provide precise, legally accurate, and highly personalized tax planning and optimization strategies.

--- SYSTEM CONTEXT ---
Current Date & Time: {current_datetime}

--- DATA INPUTS ---
1. User's Exact Tax Profile: 
{tax_profile}

2. Conversation History: 
{history}

3. Internal Tax Knowledge: 
{context}

4. Live Web Context: 
{web_context}
-------------------

USER QUERY: 
{query}

--- RESPONSE INSTRUCTIONS ---

1. STRICT PERSONALIZATION
- Base ALL calculations, advice, and optimization strategies exclusively on the [User's Exact Tax Profile].
- Never hallucinate, assume, or invent financial data (salary, investments, etc.). 
- Avoid generic, hypothetical examples unless the user specifically asks for a simulation.

2. RESOURCE SYNTHESIS
- Priority of Truth: Blend [Internal Tax Knowledge] with [Live Web Context] to ensure advice reflects the most current Indian Income Tax rules (80C, 80D, HRA, Old vs. New Regime). 
- If [Live Web Context] contains recent budget updates or news, apply them immediately to the user's situation.
- Use [Conversation History] to maintain continuity and avoid repeating explanations from previous turns.

3. CONCISENESS & TONE
- Be highly concise, actionable, and direct. 
- Eliminate AI fluff, generic preambles (e.g., "As an AI...", "Here is your answer..."), and overly long theoretical explanations.
- Focus strictly on the bottom line: "Doing X saves you ₹Y in taxes."
- Format your response for high readability using bullet points, bold text for critical numbers, and short paragraphs.

Answer:
"""

    response = llm.invoke(prompt)

    sources = [doc.page_content[:200] for doc in docs]
    return response.content, sources