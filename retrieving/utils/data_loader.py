import os
import json
from typing import List
from .models import Document


def load_documents_from_json(json_path: str, documents_folder: str) -> List[Document]:
    base_dir = os.path.dirname(os.path.abspath(__file__))  # path a utils/
    root_dir = os.path.abspath(os.path.join(base_dir, "../../"))  # path alla root del progetto

    json_path = os.path.join(root_dir, json_path)
    documents_path = os.path.join(root_dir, documents_folder)

    with open(json_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    documents = []
    for entry in entries:
        file_path = os.path.join(documents_path, entry["filename"])
        if not os.path.exists(file_path):
            print(f"Warning: file {file_path} not found.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        doc = Document(
            id=entry["filename"].replace(".txt", ""),
            filename=entry["filename"],
            title=entry["title"],
            url=entry["url"],
            metadata=entry.get("metadata", {}),
            text=text
        )
        documents.append(doc)

    return documents
