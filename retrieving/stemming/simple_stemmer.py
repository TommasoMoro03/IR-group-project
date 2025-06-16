import re

class SimpleStemmer:
    """
    In this class I tried a very simple implementation of a stemmer for italian language.
    However, this class will likely be useless.
    """
    def __init__(self):
        # Basic suffix patterns – extend as needed
        self.suffixes = sorted([
            'azione', 'azioni', 'amento', 'amenti', 'mente',
            'eremo', 'erete', 'eranno', 'erebbero',
            'evamo', 'evate', 'evano',
            'iamo', 'iate',
            'ando', 'endo',
            'are', 'ere', 'ire',
        ], key=len, reverse=True)

    def stem(self, word: str) -> str:
        """
        Logic to stem a word, if it ends with one of the suffixes and
        it has at least three other letters, then cuts the suffix.
        """
        word = word.lower()
        for suffix in sorted(self.suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def stem_tokens(self, tokens: list[str]) -> list[str]:
        return [self.stem(token) for token in tokens]

    def stem_text(self, text: str) -> list[str]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        return self.stem_tokens(tokens)
