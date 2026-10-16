import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.graph_writer import GraphWriter
from app.memory.graph_reader import GraphReader


def main():
    writer = GraphWriter()
    reader = GraphReader()

    owner_id = "graphhack_test_user"

    extracted = {
        "entities": [
            {"name": "Python", "type": "programming_language"},
            {"name": "Backend Development", "type": "field"},
        ],
        "relationships": [
            {
                "subject": "Python",
                "predicate": "USED_FOR",
                "object": "Backend Development",
                "evidence": "Python is used for Backend Development",
            }
        ],
    }

    # This test uses the existing graph writer and does not delete data.
    result = writer.save(
        extracted=extracted,
        owner_id=owner_id,
        source_message_id="graphhack_chain_test_001",
    )
    print("Write result:", result)

    facts = reader.get_multihop_facts(
        entity_name="GraphHACK",
        owner_id=owner_id,
        max_hops=2,
    )

    for fact in facts:
        print(
            f"{fact['subject']} "
            f"--[{fact['predicate']}]--> "
            f"{fact['object']}"
        )


if __name__ == "__main__":
    main()
