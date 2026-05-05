from dotenv import load_dotenv
import os

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Load env
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

# Take user input
query = input("💬 Ask a tax question: ")

# Retrieve relevant chunks
docs = db.similarity_search(query, k=3)

# Combine context
context = "\n\n".join([doc.page_content for doc in docs])

# Create sources
sources = "\n".join([f"- {doc.page_content}" for doc in docs])

# Prompt
prompt = f"""
You are a helpful Indian tax assistant.

Answer the question based ONLY on the context below.
Also provide clear explanation.

Context:
{context}

Question:
{query}

Answer:
"""

# Generate response
response = llm.invoke(prompt)

# Output
print("\n🤖 AI Answer:\n")
print(response.content)

print("\n📚 Sources:\n")
print(sources)