from nltk.stem import PorterStemmer, SnowballStemmer
from typing import List
import re

class CustomStemmer:
    def __init__(self):
        self.stemmer = SnowballStemmer("italian")

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Stems a list of tokens."""
        return [self.stemmer.stem(token) for token in tokens]

    def stem_text(self, text: str) -> List[str]:
        """Tokenizes text and then stems the tokens."""
        # Ensure consistency: use the same tokenization logic as in InvertedIndex
        tokens = re.findall(r"\b\w+\b", text.lower())
        return self.stem_tokens(tokens)