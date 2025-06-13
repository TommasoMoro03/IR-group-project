class Document:
    def __init__(self, id: str, text: str, metadata: dict = None):
        self.id = id
        self.text = text
        self.metadata = metadata if metadata is not None else {}

    def __repr__(self):
        return f"Document(id='{self.id}', text='{self.text[:50]}...', metadata={self.metadata})"
