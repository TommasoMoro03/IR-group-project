from retrieving.embedding.embedding_models import EmbeddingModel
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.indexing.vector_index import VectorIndex
from retrieving.scoring.keyword_scorer import KeywordScorer
from retrieving.scoring.vectorial_scorer import VectorialScorer
from utils.data_loader import load_documents_from_json
from utils.chunking import Chunker
from utils.storage import save_chunks_to_json, load_chunks_from_json

# GET CHUNKS (FROM JSON)
docs = load_documents_from_json("document_list.json", "documents")
"""
chunker = Chunker(chunk_size=512, overlap=30)
chunks = chunker.chunk_documents(docs)
save_chunks_to_json(chunks, "chunked_documents/chunks.json")
"""
chunks = load_chunks_from_json("chunked_documents/chunks.json")
print(f"{len(docs)} documents splitted in {len(chunks)} chunks.")

# COMPUTE EMBEDDINGS
model = EmbeddingModel()

chunk_texts = [chunk.text for chunk in chunks]
embeddings = model.encode(chunk_texts)
print(f"Computed {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")

"""
# VECTORIAL INDEXING
vector_index = VectorIndex()
vector_index.build_index(chunks, model)

# RETRIEVING
vector_scorer = VectorialScorer(vector_index, model)
query = "Doping during the Cold War"
results = vector_scorer.score(query, k=5)
print("\nTop matching chunks:")
for chunk_id, score in results:
    print(f"{chunk_id} - score: {score:.4f}")
"""

# --- build inverted index ---
inverted_index = InvertedIndex()
inverted_index.build_index(chunks)

# --- keyword BM25 scorer that uses the inverted index ---
kw_scorer = KeywordScorer(inverted_index)
query = "Agriculture"

kw_top = kw_scorer.score(query, top_k=5)

print(f"\nBM25 – Top chunks for query: '{query}'")
for cid, score in kw_top:
    print(f"{cid}: {score:.4f}")