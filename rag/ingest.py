from dotenv import load_dotenv
import os

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load env
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ OPENAI_API_KEY not found")

# Load data
loader = TextLoader("data/tax_docs/tax_info.txt")
documents = loader.load()

# Split text
text_splitter = CharacterTextSplitter(
    chunk_size=250,
    chunk_overlap=50
)

chunks = text_splitter.split_documents(documents)

# Create embeddings
embeddings = OpenAIEmbeddings()

# Create FAISS DB
db = FAISS.from_documents(chunks, embeddings)

# Save DB
db.save_local("faiss_index")

print("✅ FAISS index created and saved successfully")