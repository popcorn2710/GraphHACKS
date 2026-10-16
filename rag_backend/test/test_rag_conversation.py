import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

owner_id = "graphhack_test_user"
conversation_id = "rag_conversation_demo_001"

questions = [
    "What programming language does GraphHACK use?",
    "What is it used for?",
    "What framework does GraphHACK use?",
]

for question in questions:
    print("\n" + "=" * 60)
    print("QUESTION:", question)

    result = pipeline.answer(
        question=question,
        owner_id=owner_id,
        conversation_id=conversation_id,
    )

    print("\nANSWER:", result["answer"])
    print("RETRIEVED FACTS:", result["retrieved_fact_count"])

    for fact in result["sources"]:
        print(
            f"{fact['subject']} "
            f"--[{fact['predicate']}]--> "
            f"{fact['object']}"
        )

print("\n" + "=" * 60)
print("Conversation-aware RAG test finished.")
