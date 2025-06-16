from dataclasses import dataclass
from typing import List, Dict, Optional

# this file contains the basic structures of the few objects that will be used

@dataclass
class Document:
    id: str
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
    metadata: Dict[str, str]
