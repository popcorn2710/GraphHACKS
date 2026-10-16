import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.question_resolver import QuestionResolver

resolver = QuestionResolver()

history = [
    {
        "role": "user",
        "content": "What programming language does GraphHACK use?",
    },
    {
        "role": "assistant",
        "content": "GraphHACK uses Python for its backend.",
    },
]

question = "What is it used for?"

resolved = resolver.resolve(question, history)

print("Original question:", question)
print("Resolved question:", resolved)

assert resolved.strip().endswith("?")
print("Resolver test completed.")
