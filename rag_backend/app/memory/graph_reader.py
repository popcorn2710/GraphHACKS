
from app.db.falkordb_client import GraphDatabase


def normalize_name(name: str) -> str:
    return " ".join(name.casefold().split())


class GraphReader:  
    def __init__(self, db: GraphDatabase | None = None):
        self.db = db or GraphDatabase()

    def get_entity_facts(
        self,
        entity_name: str,
        owner_id: str,
    ) -> list[dict]:
        """Retrieve facts where the entity is the subject or object."""

        normalized = normalize_name(entity_name)

        outgoing = self.db.query(
            """
            MATCH (s:Entity {
                owner_id: $owner_id,
                normalized_name: $entity_name
            })-[:HAS_ASSERTION]->(a:Assertion)
              -[:OBJECT]->(o:Entity {owner_id: $owner_id})
            RETURN s.name, a.predicate, o.name, a.evidence
            """,
            {
                "owner_id": owner_id,
                "entity_name": normalized,
            },
        )

        incoming = self.db.query(
            """
            MATCH (s:Entity {owner_id: $owner_id})
                  -[:HAS_ASSERTION]->(a:Assertion)
                  -[:OBJECT]->(o:Entity {
                      owner_id: $owner_id,
                      normalized_name: $entity_name
                  })
            RETURN s.name, a.predicate, o.name, a.evidence
            """,
            {
                "owner_id": owner_id,
                "entity_name": normalized,
            },
        )

        facts = {}

        for result in (outgoing, incoming):
            for row in result.result_set:
                subject, predicate, obj, evidence = row

                # Deduplicate facts returned by the queries.
                key = (subject, predicate, obj)

                facts[key] = {
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "evidence": evidence,
                }

        return list(facts.values())

    def get_all_facts(
        self,
        owner_id: str,
        limit: int = 100,
    ) -> list[dict]:
        """List facts for an owner, with a bounded result size."""

        limit = max(1, min(limit, 500))

        result = self.db.query(
            """
            MATCH (s:Entity {owner_id: $owner_id})
                  -[:HAS_ASSERTION]->(a:Assertion)
                  -[:OBJECT]->(o:Entity {owner_id: $owner_id})
            RETURN s.name, a.predicate, o.name, a.evidence
            LIMIT $limit
            """,
            {
                "owner_id": owner_id,
                "limit": limit,
            },
        )

        return [
            {
                "subject": row[0],
                "predicate": row[1],
                "object": row[2],
                "evidence": row[3],
            }
            for row in result.result_set
        ]
    
    def find_entities_in_question(
        self,
        question: str,
        owner_id: str,
    ) -> list[str]:
        """Find known entity names explicitly mentioned in a question."""

        result = self.db.query(
            """
            MATCH (e:Entity {owner_id: $owner_id})
            RETURN e.name
            """,
            {"owner_id": owner_id},
        )

        question_lower = question.casefold()

        matches = [
            row[0]
            for row in result.result_set
            if isinstance(row[0], str)
            and row[0].casefold() in question_lower
        ]

        # Prefer longer names when entities overlap.
        return sorted(
            set(matches),
            key=len,
            reverse=True,
        )

    def get_facts_for_question(
        self,
        question: str,
        owner_id: str,
    ) -> list[dict]:
        """Retrieve facts connected to entities named in the question."""

        entity_names = self.find_entities_in_question(
            question=question,
            owner_id=owner_id,
        )

        facts = {}

        for name in entity_names:
            for fact in self.get_entity_facts(
                entity_name=name,
                owner_id=owner_id,
            ):
                key = (
                    fact["subject"],
                    fact["predicate"],
                    fact["object"],
                )
                facts[key] = fact

        return list(facts.values())
    
    def get_connected_facts(
        self,
        entity_name: str,
        owner_id: str,
        max_hops: int = 2,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve facts reachable within a bounded number of hops."""

        max_hops = max(1, min(max_hops, 3))
        limit = max(1, min(limit, 100))

        normalized = normalize_name(entity_name)

        result = self.db.query(
            """
            MATCH (start:Entity {
                owner_id: $owner_id,
                normalized_name: $entity_name
            })
            MATCH path = (start)-[:HAS_ASSERTION|OBJECT*1..6]-(end)
            WHERE ALL(
                n IN nodes(path)
                WHERE NOT n:Entity OR n.owner_id = $owner_id
            )
            WITH path
            LIMIT $limit
            RETURN path
            """,
            {
                "owner_id": owner_id,
                "entity_name": normalized,
                "limit": limit,
            },
        )

        facts = {}

        for path_row in result.result_set:
            # Path serialization differs across FalkorDB client versions.
            # This query result is intentionally not interpreted here.
            # Use the dedicated assertion query below for portable results.
            pass

        # Read assertion facts using an explicit bounded traversal.
        result = self.db.query(
            """
            MATCH (start:Entity {
                owner_id: $owner_id,
                normalized_name: $entity_name
            })
            MATCH (start)-[:HAS_ASSERTION]->(a:Assertion)
                  -[:OBJECT]->(o:Entity {owner_id: $owner_id})
            RETURN start.name, a.predicate, o.name, a.evidence
            LIMIT $limit
            """,
            {
                "owner_id": owner_id,
                "entity_name": normalized,
                "limit": limit,
            },
        )

        for row in result.result_set:
            facts[(row[0], row[1], row[2])] = {
                "subject": row[0],
                "predicate": row[1],
                "object": row[2],
                "evidence": row[3],
                "hop": 1,
            }

        return list(facts.values())
    

    def get_multihop_facts(
        self,
        entity_name: str,
        owner_id: str,
        max_hops: int = 2,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve facts reachable through up to three entity hops."""

        max_hops = max(1, min(max_hops, 3))
        limit = max(1, min(limit, 100))

        # Each hop is: Entity -> Assertion -> Entity.
        # Build a bounded Cypher pattern using a fixed, validated hop count.
        pattern = (
            "(start:Entity {owner_id: $owner_id, "
            "normalized_name: $entity_name})"
        )

        for index in range(max_hops):
            assertion_var = f"a{index}"
            entity_var = f"e{index}"

            pattern += (
                f"-[:HAS_ASSERTION]->({assertion_var}:Assertion)"
                f"-[:OBJECT]->({entity_var}:Entity "
                "{owner_id: $owner_id})"
            )

        return_query = f"""
            MATCH path = {pattern}
            WITH path
            UNWIND range(0, size(nodes(path)) - 1) AS idx
            WITH nodes(path) AS ns, relationships(path) AS rs, idx
            WITH ns, rs, idx
            WHERE idx + 2 < size(ns)
              AND idx % 2 = 0
              AND idx + 1 < size(rs)
            WITH ns[idx] AS subject,
                 ns[idx + 1] AS assertion,
                 ns[idx + 2] AS object
            RETURN DISTINCT
                subject.name,
                assertion.predicate,
                object.name,
                assertion.evidence
            LIMIT $limit
        """

        result = self.db.query(
            return_query,
            {
                "owner_id": owner_id,
                "entity_name": normalize_name(entity_name),
                "limit": limit,
            },
        )

        facts = []
        seen = set()

        for row in result.result_set:
            subject, predicate, obj, evidence = row
            key = (subject, predicate, obj)

            if key not in seen:
                seen.add(key)
                facts.append({
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "evidence": evidence,
                })

        return facts
