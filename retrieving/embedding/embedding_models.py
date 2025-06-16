from transformers import AutoTokenizer, AutoModel
import numpy as np
import torch
from typing import List


class EmbeddingModel:
    """
    This class is responsible for the usage of the embedding model
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        """
        Returns L2‑normalised embeddings (shape: len(texts) × hidden_dim).

        texts: list of raw strings.
        is_query: if True, prepend the “Query:” instruction required by BGE models to get optimal retrieval performance.
        """
        if not texts:
            return np.array([])

        # BGE: prepend "Query: " to queries if needed
        if is_query:
            texts = [f"Query: {text}" for text in texts]

        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            model_output = self.model(**inputs)

        token_embeddings = model_output.last_hidden_state
        attention_mask = inputs['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

        # mean‑pooling: mask padded tokens, then average
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        sentence_embeddings = sum_embeddings / sum_mask

        # normalize to unit vector
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

        return sentence_embeddings.cpu().numpy()
