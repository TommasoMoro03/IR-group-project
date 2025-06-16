import re

class SimpleStemmer:
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
