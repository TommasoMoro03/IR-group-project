from typing import List
from transformers import AutoTokenizer
from .models import Document, Chunk


class Chunker:

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", chunk_size: int = 512, overlap: int = 30):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Function that creates a list of Chunk objects for a given Document.
        """
        tokens = self.tokenizer.encode(document.text, add_special_tokens=False)
        chunks = []

        start = 0
        chunk_id = 0

        while start < len(tokens):
            # simple logic to continue creating Chunk objects until the text is finished
            end = start + self.chunk_size
            token_chunk = tokens[start:end]
            text_chunk = self.tokenizer.decode(token_chunk)

            # inherit metadata from document and adds also url and title
            chunk_metadata = document.metadata
            chunk_metadata["document_url"] = document.url
            chunk_metadata["document_title"] = document.title

            chunk = Chunk(
                id=f"{document.id}_chunk_{chunk_id}",
                doc_id=document.id,
                text=text_chunk,
                position=chunk_id,
                metadata=chunk_metadata
            )
            chunks.append(chunk)

            chunk_id += 1
            start += self.chunk_size - self.overlap

        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        Function that allows to get a list of Chunk objects from a list of Document objects.
        """
        all_chunks = []
        for doc in documents:
            doc_chunks = self.chunk_document(doc)
            all_chunks.extend(doc_chunks)
        return all_chunks
