import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.chat.chat_service import ChatService

chat = ChatService()

owner_id = "graphhack_live_test_user"
conversation_id = "live_chat_demo_001"

print("GraphHACK AI is ready!")
print("Type 'exit' or press Ctrl+C to stop.\n")

try:
    while True:
        message = input("You: ").strip()

        if message.casefold() in {"exit", "quit"}:
            print("\nGraphHACK AI: See you later!")
            break

        if not message:
            continue

        try:
            result = chat.chat(
                message=message,
                owner_id=owner_id,
                conversation_id=conversation_id,
            )

            print("\nGraphHACK AI:", result["answer"])
            print("Retrieved facts:", result["retrieved_fact_count"])
            print("Memory:", result["memory"])
            print()

        except Exception as exc:
            print(f"\nChat error: {exc}\n")

except (KeyboardInterrupt, EOFError):
    print("\n\nGraphHACK AI: Chat ended. See you next time!")
