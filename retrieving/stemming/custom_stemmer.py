from nltk.stem import PorterStemmer
from typing import List
import re

class CustomStemmer:
    def __init__(self):
        self.porter_stemmer = PorterStemmer()

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Stems a list of tokens."""
        return [self.porter_stemmer.stem(token) for token in tokens]

    def stem_text(self, text: str) -> List[str]:
        """Tokenizes text and then stems the tokens."""
        # Ensure consistency: use the same tokenization logic as in InvertedIndex
        tokens = re.findall(r"\b\w+\b", text.lower())
        return self.stem_tokens(tokens)