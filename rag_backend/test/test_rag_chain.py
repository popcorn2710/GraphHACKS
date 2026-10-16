import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.pipeline import RAGPipeline


def main():
    rag = RAGPipeline()
    owner_id = "graphhack_test_user"

    questions = [
        "What programming language does GraphHACK use?",
        "What is Python used for, given that GraphHACK uses it?",
        "What framework does GraphHACK use?",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print("QUESTION:", question)

        result = rag.answer(
            question=question,
            owner_id=owner_id,
            max_hops=2,
        )

        print("\nANSWER:", result["answer"])
        print("Retrieved facts:", result["retrieved_fact_count"])

        print("\nSOURCES:")
        for fact in result["sources"]:
            print(
                f"{fact['subject']} "
                f"--[{fact['predicate']}]--> "
                f"{fact['object']}"
            )
            print("Evidence:", fact["evidence"])


if __name__ == "__main__":
    main()
