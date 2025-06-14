from utils.data_loader import load_documents_from_json
from utils.chunking import Chunker
from utils.storage import save_chunks_to_json

docs = load_documents_from_json("document_list.json", "documents")
chunker = Chunker(chunk_size=512, overlap=30)
chunks = chunker.chunk_documents(docs)
save_chunks_to_json(chunks, "chunked_documents/chunks.json")

print(f"Chunked {len(docs)} documents into {len(chunks)} chunks.")
