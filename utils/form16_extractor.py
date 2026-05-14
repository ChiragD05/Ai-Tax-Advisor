import json
from typing import Dict, Any

from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(model="gpt-5.5", temperature=0)


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_form16_data(pdf_path: str) -> Dict[str, Any]:
    text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are extracting structured data from an Indian Form 16 PDF text dump.

Return ONLY valid JSON with these keys:
- employer_name
- employee_name
- gross_salary
- exemptions
- deductions
- taxable_income
- tds

Rules:
- If a value is not clearly available, use null.
- Return numeric values as numbers, not strings.
- Do not invent values.
- Use only the text provided.
- Keep the output strictly JSON.

PDF TEXT:
{text[:15000]}
"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # Try to clean markdown fences if present
    if raw.startswith("```"):
        raw = raw.strip("```")
        raw = raw.replace("json", "", 1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: return raw text so you can inspect
        data = {
            "employer_name": None,
            "employee_name": None,
            "gross_salary": None,
            "exemptions": None,
            "deductions": None,
            "taxable_income": None,
            "tds": None,
            "raw_llm_output": raw,
        }

    data["source_type"] = "form16"
    data["raw_text"] = text[:8000]
    return data