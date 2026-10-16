import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: GraphHACK/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the existing root-level .env file.
load_dotenv(PROJECT_ROOT / ".env")


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing {name}. Check your .env configuration."
        )
    return value


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "nemotron-mini:4b",
)

FALKORDB_HOST = required_env("FALKORDB_HOST")
FALKORDB_PORT = int(required_env("FALKORDB_PORT"))
FALKORDB_USERNAME = required_env("FALKORDB_USERNAME")
FALKORDB_PASSWORD = required_env("FALKORDB_PASSWORD")

FALKORDB_TLS = (
    os.getenv("FALKORDB_TLS", "true").lower() == "true"
)

FALKORDB_GRAPH = os.getenv(
    "FALKORDB_GRAPH",
    "ai_memory",
)