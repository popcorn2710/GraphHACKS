# GraphHACK — AI & Graph RAG System

## 1. Project Overview

GraphHACK is an AI memory and retrieval system that combines a Large Language Model (LLM), Retrieval-Augmented Generation (RAG), and a knowledge graph to provide context-aware answers grounded in stored facts.

Instead of relying entirely on the LLM's internal knowledge or repeatedly sending the entire conversation, the system stores extracted facts in a graph, retrieves relevant information when a question is asked, and uses that information to generate a response.

### Core technologies

- **LLM:** Ollama with the `nemotron-mini:4b` model
- **Knowledge graph:** FalkorDB
- **Memory representation:** Entity–Assertion–Evidence graph
- **Language:** Python
- **AI capabilities:** Fact extraction, graph retrieval, multi-hop reasoning, conversational memory, and grounded response generation

## 2. Current AI/RAG Architecture

```text
User Message
     |
     v
Conversation History
     |
     v
Memory Extraction
     |
     v
Fact Validation
     |
     v
Knowledge Graph (FalkorDB)
     |
     v
Question Understanding
     |
     v
Graph Retrieval
(Entity + Relationship + Evidence)
     |
     v
Context Construction
     |
     v
Ollama LLM
     |
     v
Grounded Response
     |
     v
Conversation Memory
```

The intended workflow combines persistent graph memory with conversation context. The question-resolution and retrieval stages still need further integration and refinement.

## 3. What Has Been Implemented

### 3.1 LLM integration

- Connected the AI system to a locally running Ollama instance.
- Implemented an LLM client in `app/llm/ollama_client.py`.
- Configured the model and Ollama endpoint through environment-based settings.
- Added error handling for failed requests and empty responses.
- Implemented non-streaming chat generation.

### 3.2 Knowledge graph memory

Implemented graph-based storage using FalkorDB.

The graph represents information using three primary node types:

- **Entity:** A person, project, technology, concept, or other identifiable item.
- **Assertion:** A relationship or fact connecting entities.
- **Evidence:** The original text supporting the assertion.

Example:

```text
(User)
   |
   | HAS_ASSERTION
   v
(Assertion: HAS_NAME)
   |
   | OBJECT
   v
(Entity: Farhaan)
```

An assertion can also link to evidence containing the original message.

Implemented capabilities:

- Deterministic identifiers for graph entities, assertions, and evidence.
- Parameterized graph queries.
- Ownership-aware graph records.
- Storage of extracted facts and their supporting evidence.
- Duplicate-resistant graph writes using deterministic IDs.

### 3.3 Automatic fact extraction

Implemented `app/memory/extractor.py`.

The extraction pipeline:

1. Sends a message to the LLM with a structured extraction prompt.
2. Extracts entities and relationships.
3. Parses the response as JSON.
4. Validates entity and relationship structures.
5. Checks relationship endpoints and predicate naming.
6. Verifies that evidence appears in the original message.

Example input:

```text
GraphHACK uses Python for its backend and FalkorDB for graph storage.
```

Expected extracted facts:

```text
GraphHACK --USES_LANGUAGE--> Python
GraphHACK --USES_DATABASE--> FalkorDB
```

The extractor also supports personal facts, such as a user's name, and study-related facts.

### 3.4 Graph writing

Implemented `app/memory/graph_writer.py`.

The graph writer:

- Creates or reuses entity nodes.
- Creates assertion and evidence records.
- Connects entities through explicit relationships.
- Associates records with an owner.
- Stores the source message identifier when available.
- Returns saved and skipped relationship counts.

### 3.5 Graph retrieval

Implemented `app/memory/graph_reader.py`.

Available operations include:

- Retrieve incoming and outgoing facts for an entity.
- Retrieve facts associated with entities mentioned in a question.
- Search known entity names in a question.
- Retrieve all facts for an owner.
- Retrieve multi-hop relationship paths.

Example:

```text
GraphHACK --USES_LANGUAGE--> Python
Python --USED_FOR--> Backend Development
```

A multi-hop query can discover that GraphHACK is connected to backend development through Python.

The current implementation supports forward relationship paths. More flexible traversal and more selective retrieval remain future improvements.

### 3.6 Persistent conversation memory

Implemented `app/memory/conversation_store.py`.

Conversation messages are stored in FalkorDB with:

- Owner ID
- Conversation ID
- Message role
- Message content
- Timestamp

The system can retrieve recent messages in chronological order. This enables conversation continuity across separate chat sessions when the same owner and stored graph are reused.

### 3.7 RAG answer generation

Implemented the main RAG workflow in `app/rag/pipeline.py`.

The pipeline currently:

1. Loads conversation history.
2. Stores the current user message.
3. Identifies potentially relevant entities.
4. Retrieves graph facts, including multi-hop facts.
5. Builds an LLM prompt containing graph context and conversation history.
6. Generates an answer through Ollama.
7. Stores the assistant's response.

Testing has demonstrated that graph facts can be retrieved and used to answer questions about previously stored information.

### 3.8 Follow-up question resolution

Implemented `app/rag/question_resolver.py`.

The resolver rewrites context-dependent questions into standalone questions.

Example:

```text
Previous context: Tell me about Python.

Follow-up: What is it used for?

Resolved question: What is Python used for?
```

The resolver has been tested independently. Its integration into the main RAG pipeline remains incomplete.

### 3.9 Hallucination control

The RAG pipeline includes a rule-based guard for certain framework-related questions.

If a question asks which framework the project uses but the retrieved facts do not provide supporting evidence, the system returns an uncertainty response rather than inventing a framework.

This is a useful initial safeguard, but it is not a complete hallucination-prevention system.

### 3.10 Initial agent architecture

The following agent-related modules have been added:

- `app/agents/base_agent.py`
- `app/agents/coordinator.py`
- `app/agents/memory_agent.py`
- `app/agents/research_agent.py`
- `app/tasks/task_manager.py`

These provide the starting structure for an agent-based architecture. Their integration, responsibilities, tool execution, and end-to-end behavior still need validation before they can be considered complete.

## 4. Validation Completed

The following behaviors have been tested during development:

- Ollama generates responses through the Python client.
- FalkorDB connectivity and graph operations work.
- Entities, assertions, and evidence can be written to the graph.
- Facts can be retrieved from the graph.
- Multi-hop retrieval works for tested relationship paths.
- Conversation messages persist across requests.
- Personal facts can be recalled from graph memory.
- Study-related facts can be recalled in a new conversation using the same owner.
- The question resolver can rewrite tested follow-up questions.
- Framework-related answers can be guarded when supporting evidence is missing.

These are development tests, not a guarantee that every possible query or agent workflow works correctly.

## 5. What Remains to Be Done

### Phase 1 — Improve question understanding

**Priority: High**

- [ ] Integrate `QuestionResolver` into `RAGPipeline.answer()`.
- [ ] Resolve pronouns and references such as "it", "that", "they", and "the previous one".
- [ ] Use the resolved question for entity detection and graph retrieval.
- [ ] Preserve conversation context without confusing the subject of the previous question.
- [ ] Test multi-turn conversations involving multiple entities.

Acceptance example:

```text
User: What is Python?
AI: Python is a programming language.

User: What is it used for?
AI: Answers specifically about Python.
```

### Phase 2 — Improve retrieval quality

**Priority: High**

- [ ] Replace broad fallback retrieval with targeted retrieval whenever possible.
- [ ] Use relationship predicates to select facts relevant to the question.
- [ ] Improve entity matching and handle aliases or alternative names.
- [ ] Support multi-hop traversal up to a maximum depth rather than requiring an exact path length.
- [ ] Consider incoming as well as outgoing paths when relevant.
- [ ] Deduplicate facts returned through overlapping graph paths.
- [ ] Rank facts by relevance to the resolved question.
- [ ] Add configurable retrieval limits to prevent excessive context.

The objective is to retrieve the smallest useful set of facts instead of sending unrelated graph information to the LLM.

### Phase 3 — Improve context construction

**Priority: High**

- [ ] Complete and validate `app/rag/context_builder.py`.
- [ ] Separate conversation history, graph facts, and evidence in the final prompt.
- [ ] Include source evidence with retrieved facts.
- [ ] Set context limits and prioritize relevant facts.
- [ ] Handle conflicting or outdated assertions.
- [ ] Clearly distinguish known facts from missing information.
- [ ] Make the LLM answer only as confidently as the available evidence permits.

### Phase 4 — Strengthen memory management

**Priority: High**

- [ ] Complete `app/memory/memory_manager.py`.
- [ ] Define rules for when a message should be converted into a persistent fact.
- [ ] Improve extraction of compound facts, such as degree, specialization, and institution.
- [ ] Preserve important details instead of reducing them to overly broad entities.
- [ ] Detect duplicate, contradictory, and superseded facts.
- [ ] Add support for updating or invalidating facts.
- [ ] Validate owner-level isolation for every graph retrieval and write.
- [ ] Define how public/shared memory differs from private user memory.

### Phase 5 — Complete the agent system

**Priority: Medium–High**

- [ ] Define the responsibility and input/output contract of each agent.
- [ ] Implement the coordinator's routing and decision-making logic.
- [ ] Connect the memory agent to extraction, retrieval, and memory updates.
- [ ] Define the research agent's allowed tools and evidence requirements.
- [ ] Implement task execution, result tracking, and error handling in the task manager.
- [ ] Decide when an agent should use graph memory, conversation history, or external research.
- [ ] Add limits to prevent endless agent loops.
- [ ] Test multi-agent execution on realistic tasks.
- [ ] Require evidence or tool results before agents make factual claims.

### Phase 6 — Build an evaluation suite

**Priority: High**

- [ ] Add automated tests for extraction accuracy.
- [ ] Test graph writes, retrieval, and conversation isolation.
- [ ] Test follow-up questions and ambiguous references.
- [ ] Test multi-hop reasoning.
- [ ] Test questions for which no answer exists in memory.
- [ ] Test contradictory facts and unsupported claims.
- [ ] Test agent failures and malformed LLM outputs.
- [ ] Measure retrieval precision, answer correctness, and response latency.
- [ ] Run regression tests whenever prompts or retrieval logic change.

### Phase 7 — Performance and reliability

**Priority: Medium**

- [ ] Reduce unnecessary LLM calls.
- [ ] Set request timeouts and consistent error handling.
- [ ] Add structured logs for retrieval decisions and agent actions.
- [ ] Track which graph facts support each answer.
- [ ] Optimize graph queries and context size.
- [ ] Evaluate streaming responses and other latency improvements.
- [ ] Add repeatable evaluation runs with a fixed test dataset.

## 6. Proposed Final AI/RAG Architecture

```text
                    User Question
                          |
                          v
                  Question Resolver
                          |
                          v
                   Intent / Task Router
                          |
             +------------+------------+
             |            |            |
             v            v            v
        Memory Agent  Research Agent  Other Agents
             |            |
             +------------+
                          |
                          v
                   Retrieval Engine
                          |
             +------------+------------+
             |                         |
             v                         v
       FalkorDB Graph             Conversation
       Memory + Evidence          History
             |                         |
             +------------+------------+
                          |
                          v
                    Context Builder
                          |
                          v
                     Ollama LLM
                          |
                          v
                  Grounded Answer
                          |
                          v
               Evidence / Source Mapping
                          |
                          v
                  Memory Update Logic
```

This is the target architecture, not a claim that every component is already integrated. External research, advanced agent routing, and full source mapping remain planned capabilities.

## 7. Recommended Implementation Order

1. Integrate question resolution into the existing RAG pipeline.
2. Make retrieval targeted and improve multi-hop traversal.
3. Finish context construction and evidence-aware answer generation.
4. Complete memory update, deduplication, and contradiction handling.
5. Validate and integrate the agent modules.
6. Build a comprehensive automated evaluation suite.
7. Optimize performance and reliability.

**Definition of done:** The AI should correctly resolve follow-up questions, retrieve only relevant graph facts, explain answers using supporting evidence, remember valid information across conversations, respect private/shared memory boundaries, and avoid inventing facts when evidence is missing.

## 8. AI/RAG Scope

This README covers only the AI and knowledge-retrieval system.

**Included:** Ollama, extraction, FalkorDB graph memory, retrieval, multi-hop reasoning, conversation memory, context construction, hallucination controls, agents, and evaluation.

**Excluded:** React/UI implementation, FastAPI/Express endpoints, authentication, deployment infrastructure, and frontend integration.

