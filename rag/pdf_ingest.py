from pypdf import PdfReader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)

    return "\n".join(text_parts)


def create_pdf_vectorstore(pdf_path: str, index_path: str):
    text = extract_text_from_pdf(pdf_path)

    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    chunks = splitter.split_text(text)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_texts(chunks, embeddings)
    db.save_local(index_path)

    return index_path