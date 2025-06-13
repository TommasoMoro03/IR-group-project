import json
from .document_parser import Document

def load_documents_from_json(filepath: str) -> list[Document]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Document(d['id'], d['text'], d['metadata']) for d in data]
