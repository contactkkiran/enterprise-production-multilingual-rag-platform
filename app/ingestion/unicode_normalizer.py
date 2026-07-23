import unicodedata


class UnicodeNormalizer:

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize Unicode text into NFKC format.
        This improves multilingual retrieval quality.
        """

        if not text:
            return ""

        return unicodedata.normalize("NFKC", text)
