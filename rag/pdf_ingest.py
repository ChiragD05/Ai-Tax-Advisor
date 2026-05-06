from pypdf import PdfReader

from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv
import os

load_dotenv()

# Read PDF
def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text


# Create FAISS DB from PDF
def create_pdf_vectorstore(pdf_path):

    text = extract_text_from_pdf(pdf_path)

    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = text_splitter.split_text(text)

    embeddings = OpenAIEmbeddings()

    db = FAISS.from_texts(chunks, embeddings)

    db.save_local("faiss_index")

    return "✅ PDF processed successfully"