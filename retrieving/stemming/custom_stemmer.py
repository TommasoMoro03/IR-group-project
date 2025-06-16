from nltk.stem import PorterStemmer, SnowballStemmer
from typing import List
import re

class CustomStemmer:
    """
    This class is a simple wrapper around an existing stemmer.
    I first used PorterStemmer but, as the documents provided are in italian,
    I switched to SnowballStemmer("italian").
    """
    def __init__(self):
        self.stemmer = SnowballStemmer("italian")

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Stems a list of tokens."""
        return [self.stemmer.stem(token) for token in tokens]

    def stem_text(self, text: str) -> List[str]:
        """Tokenizes text and then stems the tokens."""
        # of course, uses the same tokenization logic as in InvertedIndex for consistency
        tokens = re.findall(r"\b\w+\b", text.lower())
        return self.stem_tokens(tokens)