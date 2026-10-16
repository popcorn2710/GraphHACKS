
import hashlib
import re

from app.db.falkordb_client import GraphDatabase


def make_id(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_name(name: str) -> str:
    return " ".join(name.casefold().split())


class GraphWriter:
    def __init__(self, db: GraphDatabase | None = None):
        self.db = db or GraphDatabase()

    def save(
        self,
        extracted: dict,
        owner_id: str,
        source_message_id: str | None = None,
    ) -> dict:
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id is required.")

        entities = extracted.get("entities", [])
        relationships = extracted.get("relationships", [])

        entity_map = {
            normalize_name(item["name"]): item
            for item in entities
        }

        saved = 0
        skipped = 0

        for rel in relationships:
            subject_name = rel["subject"].strip()
            object_name = rel["object"].strip()
            predicate = rel["predicate"].strip().upper()
            evidence = rel["evidence"].strip()

            # Validate again at the database boundary.
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,49}", predicate):
                skipped += 1
                continue

            subject = entity_map.get(normalize_name(subject_name))
            obj = entity_map.get(normalize_name(object_name))

            if not subject or not obj or not evidence:
                skipped += 1
                continue

            subject_id = make_id(
                owner_id, normalize_name(subject_name)
            )
            object_id = make_id(
                owner_id, normalize_name(object_name)
            )

            assertion_id = make_id(
                owner_id,
                normalize_name(subject_name),
                predicate,
                normalize_name(object_name),
            )

            evidence_id = make_id(
                owner_id,
                source_message_id or "",
                evidence,
            )

            self.db.query(
                """
                MERGE (s:Entity {id: $subject_id})
                ON CREATE SET
                    s.name = $subject_name,
                    s.normalized_name = $subject_norm,
                    s.entity_type = $subject_type,
                    s.owner_id = $owner_id

                MERGE (o:Entity {id: $object_id})
                ON CREATE SET
                    o.name = $object_name,
                    o.normalized_name = $object_norm,
                    o.entity_type = $object_type,
                    o.owner_id = $owner_id

                MERGE (a:Assertion {id: $assertion_id})
                ON CREATE SET
                    a.owner_id = $owner_id,
                    a.predicate = $predicate,
                    a.evidence = $evidence

                SET
                    a.evidence = $evidence,
                    a.source_message_id = $source_message_id

                MERGE (s)-[:HAS_ASSERTION]->(a)
                MERGE (a)-[:OBJECT]->(o)

                MERGE (e:Evidence {id: $evidence_id})
                ON CREATE SET
                    e.owner_id = $owner_id,
                    e.content = $evidence,
                    e.source_message_id = $source_message_id

                MERGE (a)-[:SUPPORTED_BY]->(e)
                """,
                {
                    "subject_id": subject_id,
                    "subject_name": subject["name"],
                    "subject_norm": normalize_name(subject["name"]),
                    "subject_type": subject["type"],
                    "object_id": object_id,
                    "object_name": obj["name"],
                    "object_norm": normalize_name(obj["name"]),
                    "object_type": obj["type"],
                    "assertion_id": assertion_id,
                    "owner_id": owner_id,
                    "predicate": predicate,
                    "evidence": evidence,
                    "source_message_id": source_message_id,
                    "evidence_id": evidence_id,
                },
            )

            saved += 1

        return {
            "saved_relationships": saved,
            "skipped_relationships": skipped,
        }
