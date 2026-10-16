
import time
import uuid

from app.db.falkordb_client import GraphDatabase


class ConversationStore:
    def __init__(self, db=None):
        self.db = db or GraphDatabase()

    def save_message(
        self,
        owner_id: str,
        conversation_id: str,
        role: str,
        content: str,
    ) -> dict:
        if not owner_id.strip():
            raise ValueError("owner_id is required.")

        if not conversation_id.strip():
            raise ValueError("conversation_id is required.")

        if role not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'.")

        if not content.strip():
            raise ValueError("Message content cannot be empty.")

        message_id = str(uuid.uuid4())
        created_at = time.time()

        self.db.query(
            """
            CREATE (m:ConversationMessage {
                message_id: $message_id,
                owner_id: $owner_id,
                conversation_id: $conversation_id,
                role: $role,
                content: $content,
                created_at: $created_at
            })
            """,
            {
                "message_id": message_id,
                "owner_id": owner_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": created_at,
            },
        )

        return {
            "message_id": message_id,
            "role": role,
            "content": content,
            "created_at": created_at,
        }

    def get_history(
        self,
        owner_id: str,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        if not owner_id.strip() or not conversation_id.strip():
            raise ValueError(
                "owner_id and conversation_id are required."
            )

        limit = max(1, min(limit, 50))

        result = self.db.query(
            """
            MATCH (m:ConversationMessage {
                owner_id: $owner_id,
                conversation_id: $conversation_id
            })
            RETURN m.role, m.content, m.created_at
            ORDER BY m.created_at DESC
            LIMIT $limit
            """,
            {
                "owner_id": owner_id,
                "conversation_id": conversation_id,
                "limit": limit,
            },
        )

        # The database returns newest first.
        # Reverse the results so the LLM sees oldest first.
        messages = [
            {
                "role": row[0],
                "content": row[1],
                "created_at": row[2],
            }
            for row in result.result_set
        ]

        messages.reverse()
        return messages
