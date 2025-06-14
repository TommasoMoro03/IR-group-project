from retrieving.embedding.embedding_models import EmbeddingModel
from retrieving.hybrid_retriever.hybrid_retriever import HybridRetriever
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

# VECTORIAL INDEXING
vector_index = VectorIndex()
vector_index.build_index(chunks, model)

"""
# RETRIEVING
vector_scorer = VectorialScorer(vector_index, model)
query = "Doping during the Cold War"
results = vector_scorer.score(query, k=5)
print("\nTop matching chunks:")
for chunk_id, score in results:
    print(f"{chunk_id} - score: {score:.4f}")
"""

# (1) vector scorer
vector_scorer = VectorialScorer(vector_index, model)

# (2) inverted index + keyword scorer
inv = InvertedIndex()
inv.build_index(chunks)
keyword_scorer = KeywordScorer(inv)

# (3) hybrid retriever (es: alpha = 0.6 → more importance on vector)
hybrid = HybridRetriever(vector_scorer, keyword_scorer, alpha=0.9)

# ----------------- TEST -----------------
query = "Agricultural policy in Brazil"
results = hybrid.search(query, top_k=5)

print(f"\nHybrid results for query: '{query}' (α=0.6)")
for cid, h, v, k in results:
    print(f"{cid} | hybrid={h:.3f} | vec={v:.3f} | key={k:.3f}")