from dotenv import load_dotenv
import os

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ OPENAI_API_KEY not found")

# Initialize models
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Load FAISS DB
db = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

print("✅ AI Tax Assistant Ready\n")

# User input
query = input("💬 Ask a tax question: ")

# Retrieve top chunks
docs = db.similarity_search(query, k=3)

# Build context with numbering
context_list = []
for i, doc in enumerate(docs):
    context_list.append(f"[{i+1}] {doc.page_content}")

context = "\n\n".join(context_list)

# Prompt (IMPROVED)
prompt = f"""
You are an expert Indian tax assistant.

Answer the user's question using ONLY the context below.

Rules:
- Give a clear and concise answer
- Mention section names (like 80C, 80D)
- Use bullet points if needed
- Cite sources using [1], [2], etc.
- If unsure, say "I don't know"

Context:
{context}

Question:
{query}

Answer:
"""

# Generate answer
response = llm.invoke(prompt)

# Output answer
print("\n🤖 AI Answer:\n")
print(response.content)

# Print sources separately
print("\n📚 Sources:\n")
for i, doc in enumerate(docs):
    print(f"[{i+1}] {doc.page_content}\n")