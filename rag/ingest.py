from dotenv import load_dotenv
import os

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")
loader = TextLoader("data/tax_docs/tax_info.txt")
documents=loader.load()

text_splitter = CharacterTextSplitter(
    separator=" ", 
    chunk_size=250, 
    chunk_overlap=50
)


chunks = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(chunks, embeddings)
db.save_local("faiss_index")
print("✅ FAISS index created and saved successfully")