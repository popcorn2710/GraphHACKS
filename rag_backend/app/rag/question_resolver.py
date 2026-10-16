
from app.llm.ollama_client import OllamaClient


RESOLVER_PROMPT = """
You rewrite follow-up questions into standalone questions.

Rules:
1. Use conversation history to resolve pronouns like it, they, this,
   that, and those.
2. Preserve the user's intended meaning.
3. Do not answer the question.
4. Do not invent facts or entities.
5. If the reference is genuinely ambiguous, return the original
   question unchanged.
6. Return ONLY the rewritten question, with no explanation.

Example:
History:
User: What programming language does GraphHACK use?
Assistant: GraphHACK uses Python.

Follow-up: What is it used for?
Rewritten question: What is Python used for?
"""


class QuestionResolver:
    def __init__(self, llm=None):
        self.llm = llm or OllamaClient()

    def resolve(self, question: str, history: list[dict]) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        conversation = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history[-10:]
        )

        result = self.llm.chat(
            [
                {
                    "role": "system",
                    "content": RESOLVER_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation history:\n{conversation or '(empty)'}"
                        f"\n\nFollow-up question: {question}\n"
                        "\nRewrite the question only."
                    ),
                },
            ],
            temperature=0,
        )

        # Keep the original question if the model returns nothing.
        return result.strip() or question.strip()
