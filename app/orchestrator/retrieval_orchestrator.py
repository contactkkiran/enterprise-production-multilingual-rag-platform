import re
from typing import Optional


class RetrievalOrchestrator:
    """
    Determines the appropriate retrieval strategy
    based on the user query.
    """

    def extract_policy_id(self, query: str) -> Optional[str]:
        """
        Extract the full policy identifier from the user query.

        Examples:
            CAR-120
            MED-500
            LIFE-101
        """

        match = re.search(r"\b([A-Z]+-\d+)\b", query.upper())

        if match:
            return match.group(1)

        return None

    def extract_policy_prefix(self, query: str) -> Optional[str]:
        """
        Extract the policy prefix from the user query.

        Examples:
            CAR-120   -> CAR
            MED-500   -> MED
            LIFE-101  -> LIFE

        Args:
            query: User query.

        Returns:
            Policy prefix if found; otherwise None.
        """

        policy_id = self.extract_policy_id(query)

        if policy_id:
            return policy_id.split("-", maxsplit=1)[0]

        return None

    def determine_strategy(self, query: str) -> str:
        """
        Determine which retrieval strategy should be used.

        Returns:
            BM25      -> When a structured policy identifier exists.
            SEMANTIC  -> When the query is purely natural language.
        """

        policy_prefix = self.extract_policy_prefix(query)

        if policy_prefix:
            return "BM25"

        return "SEMANTIC"


if __name__ == "__main__":

    orchestrator = RetrievalOrchestrator()

    queries = [
        "Does CAR-120 cover engine damage?",
        "Show policy MED-500",
        "Explain engine damage coverage",
        "What are the exclusions for travel insurance?",
    ]

    for query in queries:

        print("=" * 80)
        print(f"Query    : {query}")
        print(f"Prefix   : {orchestrator.extract_policy_prefix(query)}")
        print(f"Strategy : {orchestrator.determine_strategy(query)}")
