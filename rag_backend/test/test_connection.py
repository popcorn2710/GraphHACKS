import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.falkordb_client import GraphDatabase
from app.llm.ollama_client import OllamaClient


def test_ollama():
    print("\n[1/2] Testing Ollama...")

    llm = OllamaClient()

    answer = llm.chat([
        {
            "role": "user",
            "content": "Reply with exactly: OLLAMA_OK",
        }
    ])

    print("Ollama response:", answer)


def test_falkordb():
    print("\n[2/2] Testing FalkorDB...")

    db = GraphDatabase()

    result = db.query(
        "RETURN 1 AS healthy"
    )

    print("FalkorDB query succeeded:", result)


if __name__ == "__main__":
    test_ollama()
    test_falkordb()

    print("\nBoth connection tests completed.")