from dotenv import load_dotenv
import os

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

db = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

def get_tax_answer(query):
    docs = db.similarity_search(query, k=3)

    context_list = []
    for i, doc in enumerate(docs):
        context_list.append(f"[{i+1}] {doc.page_content}")

    context = "\n\n".join(context_list)

    prompt = f"""
    You are an expert Indian tax assistant.

    Answer using ONLY the context below.
    Cite sources like [1], [2].

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    response = llm.invoke(prompt)

    sources = [doc.page_content for doc in docs]

    return response.content, sources