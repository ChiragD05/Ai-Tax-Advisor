from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings()

db = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


def get_tax_answer(
    query,
    chat_history=None,
    tax_context=None
):

    chat_history = chat_history or []
    tax_context = tax_context or {}

    docs = db.similarity_search(query, k=3)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    history = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in chat_history
    ])


    # =========================================
    # TAX CONTEXT
    # =========================================

    tax_profile = ""

    if tax_context:

        tax_profile = f"""
CURRENT USER TAX PROFILE:

Salary: ₹{tax_context.get('salary', 0):,.0f}

Current Tax Regime:
{tax_context.get('regime', '')}

Total Selected Deductions:
₹{tax_context.get('selected_total', 0):,.0f}

Deduction Breakdown:
{tax_context.get('deduction_breakdown', {})}

Calculated Old Regime Tax:
₹{tax_context.get('old_tax', 0):,.2f}

Calculated New Regime Tax:
₹{tax_context.get('new_tax', 0):,.2f}

Best Regime:
{tax_context.get('best_regime', '')}

IMPORTANT:
You MUST use these tax values directly.
DO NOT assume taxable income.
DO NOT invent salary numbers.
DO NOT create hypothetical examples unless user asks.
"""



    # =========================================
    # FINAL PROMPT
    # =========================================

    prompt = f"""
You are an expert Indian tax advisor.

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

User Question:
{query}

Instructions:
- Use the exact calculated values from the tax profile
- Never assume salary or taxable income
- Never create hypothetical examples unless asked
- Answer specifically for THIS user
- Keep answers practical and conversational

Answer:
"""

    response = llm.invoke(prompt)

    sources = [
        doc.page_content[:200]
        for doc in docs
    ]

    return response.content, sources