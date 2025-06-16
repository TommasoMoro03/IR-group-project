import os
import json
from typing import List
from .models import Document


def load_documents_from_json(json_path: str, documents_folder: str) -> List[Document]:
    """
    Function to load documents from json file.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # path to utils/
    root_dir = os.path.abspath(os.path.join(base_dir, "../../"))  # path to the project root

    json_path = os.path.join(root_dir, json_path)
    documents_path = os.path.join(root_dir, documents_folder)

    # opening the json file
    with open(json_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    documents = []
    for entry in entries:
        # retrieve the filename (the file is inside the documents folder)
        file_path = os.path.join(documents_path, entry["filename"])
        if not os.path.exists(file_path):
            print(f"Warning: file {file_path} not found.")
            continue

        # opens the txt file
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # creates a Document object
        doc = Document(
            # the id is simply the filename without the extension
            id=entry["filename"].replace(".txt", ""),
            filename=entry["filename"],
            title=entry["title"],
            url=entry["url"],
            metadata=entry.get("metadata", {}),
            text=text
        )
        documents.append(doc)

    return documents
