import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.extractor import MemoryExtractor
from app.memory.graph_writer import GraphWriter

owner_id = "graphhack_intro_test_user"

extractor = MemoryExtractor()
writer = GraphWriter()

message = "I am Farhaan"

extracted = extractor.extract(message)

print("EXTRACTED:")
print(extracted)

result = writer.save(
    extracted=extracted,
    owner_id=owner_id,
    source_message_id="intro_test_001",
)

print("\nSAVE RESULT:")
print(result)

assert result["saved_relationships"] >= 1, (
    "No relationship was saved. Check the extractor output and prompt."
)

print("\nIntroduction memory test passed!")
