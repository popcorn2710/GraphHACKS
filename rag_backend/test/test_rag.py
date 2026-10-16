import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.pipeline import RAGPipeline


def main():
    rag = RAGPipeline()
    owner_id = "graphhack_test_user"

    questions = [
        "Which programming language does GraphHACK use?",
        "Which database does GraphHACK use?",
        "Which frontend framework does GraphHACK use?",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print("QUESTION:", question)

        result = rag.answer(
            question=question,
            owner_id=owner_id,
        )

        print("\nANSWER:", result["answer"])
        print(
            "Retrieved facts:",
            result["retrieved_fact_count"],
        )

        print("\nSOURCES:")
        for source in result["sources"]:
            print(
                f"- {source['subject']} "
                f"--[{source['predicate']}]--> "
                f"{source['object']}"
            )
            print(f"  Evidence: {source['evidence']}")


if __name__ == "__main__":
    main()
