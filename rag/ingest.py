from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

loader = TextLoader("data/tax_docs/tax_info.txt")
documents=loader.load()

text_splitter = CharacterTextSplitter(
    separator=" ", 
    chunk_size=250, 
    chunk_overlap=50
)


chunks = text_splitter.split_documents(documents)

# 4. Print the result
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk.page_content}\n")