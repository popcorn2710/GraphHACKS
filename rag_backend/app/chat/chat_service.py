
import uuid

from app.memory.extractor import MemoryExtractor
from app.memory.graph_writer import GraphWriter
from app.rag.pipeline import RAGPipeline


class ChatService:
    def __init__(self):
        self.extractor = MemoryExtractor()
        self.writer = GraphWriter()
        self.pipeline = RAGPipeline()

    def chat(
        self,
        message: str,
        owner_id: str,
        conversation_id: str,
    ) -> dict:
        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        message = message.strip()
        memory_result = {
            "saved_relationships": 0,
            "skipped_relationships": 0,
        }

        # Simple first-pass filter: don't extract from direct questions.
        # We'll improve this as the chat system develops.
        if not message.endswith("?"):
            try:
                extracted = self.extractor.extract(message)

                memory_result = self.writer.save(
                    extracted=extracted,
                    owner_id=owner_id,
                    source_message_id=str(uuid.uuid4()),
                )
            except Exception as exc:
                # Memory extraction failure should not prevent chatting.
                memory_result["memory_error"] = str(exc)

        # The existing pipeline handles conversation history,
        # question resolution, graph retrieval, and the answer.
        
        if self.is_small_talk(message):
            response = self.pipeline.llm.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are GraphHACK AI. Respond naturally "
                            "to greetings and casual conversation. "
                            "Do not claim to remember facts unless "
                            "they have actually been saved."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.4,
            )

            self.pipeline.conversations.save_message(
                owner_id=owner_id,
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            self.pipeline.conversations.save_message(
                owner_id=owner_id,
                conversation_id=conversation_id,
                role="assistant",
                content=response,
            )

            return {
                "question": message,
                "answer": response,
                "conversation_id": conversation_id,
                "retrieved_fact_count": 0,
                "sources": [],
                "memory": memory_result,
            }

        result = self.pipeline.answer(
            question=message,
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        result["memory"] = memory_result
        return result
    
    def is_small_talk(self, message: str) -> bool:
        text = message.strip().casefold()

        greetings = {
            "hi",
            "hello",
            "hey",
            "hello!",
            "hi!",
            "hey!",
            "good morning",
            "good afternoon",
            "good evening",
        }

        return text in greetings
