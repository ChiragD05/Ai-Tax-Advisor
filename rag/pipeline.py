from dotenv import load_dotenv
import os

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)



def get_tax_answer(query, chat_history=[]):
    db = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
    )
    docs = db.similarity_search(query, k=3)

    context_list = []
    for i, doc in enumerate(docs):
        context_list.append(f"[{i+1}] {doc.page_content}")

    context = "\n\n".join(context_list)
    history = ""

    for msg in chat_history:
      role  = msg["role"]
      content = msg["content"]
      history += f"{role}: {content}\n"

    prompt = f"""
    You are an expert Indian tax assistant.

    Previous Conversation:
    {history}

    Context:
    {context} 

    Question:
    {query}

    Answer:
    """

    response = llm.invoke(prompt)

    sources = [doc.page_content for doc in docs]

    return response.content, sources