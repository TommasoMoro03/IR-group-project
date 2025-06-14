import json
import os
from typing import List
from .models import Chunk


def save_chunks_to_json(chunks: List[Chunk], filepath: str) -> None:
    # crea la directory se non esiste
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    serializable_chunks = [
        {
            "id": chunk.id,
            "doc_id": chunk.doc_id,
            "text": chunk.text,
            "position": chunk.position,
            "metadata": chunk.metadata
        }
        for chunk in chunks
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable_chunks, f, ensure_ascii=False, indent=2)


def load_chunks_from_json(filepath: str) -> List[Chunk]:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        Chunk(
            id=item["id"],
            doc_id=item["doc_id"],
            text=item["text"],
            position=item["position"],
            metadata=item["metadata"]
        )
        for item in data
    ]
