from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Document:
    id: str  # unique identifier, maybe filename without extension
    filename: str
    title: str
    url: str
    metadata: Dict[str, str]
    text: str


@dataclass
class Chunk:
    id: str
    doc_id: str
    text: str
    position: int  # position of chunk in original doc
    metadata: Dict[str, str]  # inherit from document


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
    matched_terms: Optional[List[str]] = None  # for keyword highlighting
