from langdetect import LangDetectException, detect


class LanguageDetector:
    """
    Detects the primary language of a document.
    """

    @staticmethod
    def detect(text: str) -> str:

        if not text:
            return "unknown"

        try:
            return detect(text)

        except LangDetectException:
            return "unknown"
    