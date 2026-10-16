import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.graph_reader import GraphReader


def main():
    reader = GraphReader()

    facts = reader.get_connected_facts(
        entity_name="GraphHACK",
        owner_id="graphhack_test_user",
        max_hops=2,
    )

    print(f"Retrieved {len(facts)} connected facts")

    for fact in facts:
        print(
            f"{fact['subject']} "
            f"--[{fact['predicate']}]--> "
            f"{fact['object']}"
        )
        print("Evidence:", fact["evidence"])


if __name__ == "__main__":
    main()
