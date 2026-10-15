
import os
import re
import json
import uuid
import requests

from datetime import datetime, timezone
from dotenv import load_dotenv
from falkordb import FalkorDB


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL", "http://localhost:11434"
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL", "qwen3.5:latest"
)

FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME") or None
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD") or None
FALKORDB_TLS = os.getenv(
    "FALKORDB_TLS", "false"
).lower() == "true"

db = FalkorDB(
    host=FALKORDB_HOST,
    port=FALKORDB_PORT,
    username=FALKORDB_USERNAME,
    password=FALKORDB_PASSWORD,
    ssl=FALKORDB_TLS,
    socket_connect_timeout=5,
    socket_timeout=10,
)

graph = db.select_graph("RAG2")


def now():
    return datetime.now(timezone.utc).isoformat()


def run_query(query, params=None):
    """Run a parameterized FalkorDB Cypher query."""
    return graph.query(query, params or {})


# ==================================================
# 2. OLLAMA
# ==================================================

def call_ollama(messages, json_mode=False):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "think": False
    }

    if json_mode:
        payload["format"] = "json"

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=180,
    )
    response.raise_for_status()

    result = response.json()
    return result["message"]["content"]


# ==================================================
# 3. USER AND MESSAGE STORAGE
# ==================================================

def save_message(user_id, content, role="user"):
    message_id = str(uuid.uuid4())
    timestamp = now()

    # Create the user if it does not exist.
    run_query(
        """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.created_at = $timestamp
        """,
        {
            "user_id": str(user_id),
            "timestamp": timestamp,
        },
    )

    run_query(
        """
        CREATE (m:Message {
            id: $message_id,
            owner_id: $user_id,
            content: $content,
            role: $role,
            created_at: $timestamp
        })
        WITH m
        MATCH (u:User {id: $user_id})
        CREATE (u)-[:HAS_MESSAGE]->(m)
        """,
        {
            "message_id": message_id,
            "user_id": str(user_id),
            "content": content,
            "role": role,
            "timestamp": timestamp,
        },
    )

    return message_id


def get_history(user_id, limit=10):
    result = run_query(
        """
        MATCH (u:User {id: $user_id})-[:HAS_MESSAGE]->(m:Message)
        RETURN m.content, m.role, m.created_at
        ORDER BY m.created_at DESC
        LIMIT $limit
        """,
        {
            "user_id": str(user_id),
            "limit": limit,
        },
    )

    # Return oldest to newest for the LLM.
    rows = list(reversed(result.result_set))

    return [
        {
            "role": row[1],
            "content": row[0],
        }
        for row in rows
    ]


# ==================================================
# 4. EXTRACT ENTITIES AND RELATIONSHIPS
# ==================================================

def extract_graph_data(message, user_id, context=None):
    prompt = """
Extract explicit facts and relationships from the latest message.

Return JSON in this exact shape:
{
  "entities": [
    {"id": "e1", "name": "BTech", "type": "Degree"}
  ],
  "relationships": [
    {
      "subject": "user",
      "predicate": "STUDIES",
      "object": "e1",
      "evidence": "I study BTech"
    }
  ]
}

Rules:
- "user" represents the authenticated speaker.
- Use "user" as the subject for explicit first-person facts.
- Use local IDs e1, e2, etc. for other entities.
- Every subject and object must be "user" or a declared entity ID.
- Extract only reliable facts supported by the latest message.
- Use conversation context only to resolve unambiguous pronouns.
- Do not extract old context facts as if they were stated again.
- Do not invent names, colleges, locations, or relationships.
- Predicates are short uppercase action or relation names.
- Examples: STUDIES, BUILDS, USES, LIKES, DEPENDS_ON.
- A predicate must match [A-Z][A-Z0-9_]*.
- Entity types should be concise, e.g. Person, Degree, Skill,
  College, Place, Organization, Hobby, Project.
- Evidence must be an exact quote from the latest message.
- If there are no reliable facts, return empty arrays.
- Output valid JSON only.
"""

    content = call_ollama(
        [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Authenticated user ID: {user_id}\n"
                    f"Conversation context:\n{context or '(none)'}\n\n"
                    f"Latest message:\n{message}"
                ),
            },
        ],
        json_mode=True,
    )

    data = json.loads(content)

    if not isinstance(data.get("entities"), list):
        raise ValueError("Invalid entities in model response")

    if not isinstance(data.get("relationships"), list):
        raise ValueError("Invalid relationships in model response")

    return data


# ==================================================
# 5. SAVE ENTITIES AND FACTS
# ==================================================

def save_graph_data(user_id, message_id, original_message, data):
    user_id = str(user_id)

    # Local LLM IDs map to stable entity names.
    entity_ids = {"user": None}

    for entity in data.get("entities", []):
        local_id = entity.get("id")
        name = entity.get("name")
        entity_type = entity.get("type", "Thing")

        if not isinstance(local_id, str):
            continue

        if not re.fullmatch(r"e[0-9]+", local_id):
            continue

        if not isinstance(name, str) or not name.strip():
            continue

        if not isinstance(entity_type, str):
            entity_type = "Thing"

        name = name.strip()
        entity_type = entity_type.strip()[:60] or "Thing"
        normalized_name = name.casefold()

        run_query(
            """
            MERGE (e:Entity {
                owner_id: $user_id,
                normalized_name: $normalized_name
            })
            ON CREATE SET
                e.id = $entity_id,
                e.name = $name,
                e.entity_type = $entity_type,
                e.created_at = $timestamp
            """,
            {
                "user_id": user_id,
                "normalized_name": normalized_name,
                "entity_id": str(uuid.uuid4()),
                "name": name,
                "entity_type": entity_type,
                "timestamp": now(),
            },
        )

        entity_ids[local_id] = normalized_name

    # Create one Fact node per supported assertion.
    # Fact nodes allow messages to link to evidence without
    # attempting to use a relationship as another edge endpoint.
    for relation in data.get("relationships", []):
        if not isinstance(relation, dict):
            continue

        subject = relation.get("subject")
        predicate = relation.get("predicate")
        obj = relation.get("object")
        evidence = relation.get("evidence")

        if subject not in entity_ids or obj not in entity_ids:
            continue

        if subject == obj:
            continue

        if not isinstance(predicate, str):
            continue

        predicate = predicate.strip().upper()

        # Dynamic predicates are stored as data, not Cypher syntax.
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,59}", predicate):
            continue

        if not isinstance(evidence, str) or not evidence.strip():
            continue

        evidence = evidence.strip()

        # Evidence must exactly occur in the current message.
        if evidence not in original_message:
            continue

        subject_key = entity_ids[subject]
        object_key = entity_ids[obj]

        # Build parameterized MATCH clauses for both endpoints.
        query = """
        MATCH (m:Message {
            id: $message_id,
            owner_id: $user_id
        })
        """

        if subject == "user":
            query += """
            MATCH (s:User {id: $user_id})
            """
        else:
            query += """
            MATCH (s:Entity {
                owner_id: $user_id,
                normalized_name: $subject_key
            })
            """

        if obj == "user":
            query += """
            MATCH (o:User {id: $user_id})
            """
        else:
            query += """
            MATCH (o:Entity {
                owner_id: $user_id,
                normalized_name: $object_key
            })
            """

        query += """
        CREATE (fact_node:Fact {
            id: $fact_id,
            owner_id: $user_id,
            predicate: $predicate,
            evidence: $evidence,
            message_id: $message_id,
            created_at: $timestamp
        })
        CREATE (s)-[:SUBJECT_OF]->(fact_node)
        CREATE (fact_node)-[:OBJECT_OF]->(o)
        CREATE (m)-[:ASSERTS]->(fact_node)
        """
        run_query(
            query,
            {
                "message_id": message_id,
                "user_id": user_id,
                "subject_key": subject_key,
                "object_key": object_key,
                "fact_id": str(uuid.uuid4()),
                "predicate": predicate,
                "evidence": evidence,
                "timestamp": now(),
            },
        )


# ==================================================
# 6. READ GRAPH MEMORY
# ==================================================

def get_memory(user_id, limit=30):
    result = run_query(
        """
        MATCH (s)-[:SUBJECT_OF]->(f:Fact {
            owner_id: $user_id
        })-[:OBJECT_OF]->(o)
        RETURN
            CASE WHEN s:User THEN 'user'
                 ELSE s.name END AS subject,
            f.predicate AS predicate,
            CASE WHEN o:User THEN 'user'
                 ELSE o.name END AS object,
            f.evidence AS evidence
        ORDER BY f.created_at DESC
        LIMIT $limit
        """,
        {
            "user_id": str(user_id),
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


# ==================================================
# 7. CHAT
# ==================================================

def chat(user_id, message):
    user_id = str(user_id)

    # Capture previous context before saving the new message.
    history = get_history(user_id, limit=10)

    context = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )

    # Persist the user's message.
    message_id = save_message(
        user_id,
        message,
        role="user",
    )

    # Extract and save explicit facts.
    try:
        data = extract_graph_data(
            message,
            user_id,
            context=context,
        )

        save_graph_data(
            user_id,
            message_id,
            message,
            data,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Memory extraction warning: {exc}")
    except requests.RequestException as exc:
        print(f"Ollama connection warning: {exc}")

    # Retrieve the latest graph facts.
    memory = get_memory(user_id, limit=30)

    memory_text = json.dumps(
        memory,
        ensure_ascii=False,
        indent=2,
    )

    # Generate the answer using conversation and graph memory.
    answer = call_ollama(
        [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant with persistent "
                    "knowledge-graph memory.\n"
                    "Use the supplied graph memory and conversation "
                    "history when relevant.\n"
                    "Do not claim a fact is known if the memory does "
                    "not support it.\n\n"
                    f"Graph memory:\n{memory_text}"
                ),
            },
            *history,
            {"role": "user", "content": message},
        ]
    )

    save_message(
        user_id,
        answer,
        role="assistant",
    )

    return answer


# ==================================================
# 8. TERMINAL ENTRY POINT
# ==================================================

def main():
    user_id = input("User ID (e.g. farhaan): ").strip()

    if not user_id:
        print("User ID cannot be empty.")
        return

    print("\nAI Memory Chat")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            message = input("You: ").strip()

            if message.lower() in {"exit", "quit"}:
                break

            if not message:
                continue

            answer = chat(user_id, message)
            print(f"\nAI: {answer}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except requests.RequestException as exc:
            print(f"Connection error: {exc}")

        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
