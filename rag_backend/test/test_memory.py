import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import json

from app.memory.extractor import MemoryExtractor
from app.memory.graph_writer import GraphWriter


def main():
    message = (
        "GraphHACK uses Python for its backend "
        "and FalkorDB for graph storage."
    )

    owner_id = "graphhack_test_user"

    print("\n[1/3] Extracting facts from the message...")

    extractor = MemoryExtractor()
    extracted = extractor.extract(message)

    print(json.dumps(extracted, indent=2))

    if not extracted["relationships"]:
        print("No relationships extracted. Nothing was written.")
        return

    print("\n[2/3] Saving facts into FalkorDB...")

    writer = GraphWriter()
    result = writer.save(
        extracted=extracted,
        owner_id=owner_id,
        source_message_id="graphhack_test_message_001",
    )

    print("Write result:", result)

    print("\n[3/3] Verifying saved assertions...")

    verification = writer.db.query(
        """
        MATCH (s:Entity)-[:HAS_ASSERTION]->(a:Assertion)
              -[:OBJECT]->(o:Entity)
        WHERE a.owner_id = $owner_id
        RETURN s.name, a.predicate, o.name, a.evidence
        LIMIT 20
        """,
        {"owner_id": owner_id},
    )

    for row in verification.result_set:
        print("FACT:", row)

    print("\nMemory test completed.")


if __name__ == "__main__":
    main()
