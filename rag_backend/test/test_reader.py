import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.graph_reader import GraphReader


def main():
    reader = GraphReader()
    owner_id = "graphhack_test_user"

    print("\n[1/3] Looking up GraphHACK...")

    facts = reader.get_entity_facts(
        entity_name="GraphHACK",
        owner_id=owner_id,
    )

    for fact in facts:
        print(
            f"{fact['subject']} "
            f"--[{fact['predicate']}]--> "
            f"{fact['object']}"
        )
        print("Evidence:", fact["evidence"])

    print("\n[2/3] Looking up Python...")

    python_facts = reader.get_entity_facts(
        entity_name="Python",
        owner_id=owner_id,
    )

    for fact in python_facts:
        print(
            f"{fact['subject']} "
            f"--[{fact['predicate']}]--> "
            f"{fact['object']}"
        )

    print("\n[3/3] Listing all stored facts...")

    all_facts = reader.get_all_facts(owner_id)

    print(f"Retrieved {len(all_facts)} facts.")

    for fact in all_facts:
        print(fact)


if __name__ == "__main__":
    main()
