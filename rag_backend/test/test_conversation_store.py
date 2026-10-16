import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.conversation_store import ConversationStore

store = ConversationStore()

owner_id = "graphhack_test_user"
conversation_id = "conversation_test_001"

# Save a small conversation.
store.save_message(
    owner_id,
    conversation_id,
    "user",
    "What programming language does GraphHACK use?",
)

store.save_message(
    owner_id,
    conversation_id,
    "assistant",
    "GraphHACK uses Python for its backend.",
)

store.save_message(
    owner_id,
    conversation_id,
    "user",
    "What is it used for?",
)

# Read the conversation back.
history = store.get_history(
    owner_id=owner_id,
    conversation_id=conversation_id,
    limit=10,
)

print("\n=== CONVERSATION HISTORY ===")

for message in history:
    print(f"{message['role'].upper()}: {message['content']}")

assert len(history) == 3
assert history[0]["role"] == "user"
assert history[1]["role"] == "assistant"
assert history[2]["content"] == "What is it used for?"

print("\nConversation storage test passed!")
