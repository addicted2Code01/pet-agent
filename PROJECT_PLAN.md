# Project Plan: Pet Sitter AI Agent

## 1. Overview
A "Local-First" AI agent designed to assist pet sitters with instructions, schedules, and emergency protocols. The system ensures privacy by running entirely on the user's local network, utilizing a local LLM endpoint.

## 2. Core Objectives
- **Privacy & Security:** No sensitive home or pet data leaves the local network.
- **Reliability:** Provide clear, unambiguous instructions for medication, feeding, and household items.
- **Extensibility:** Use the Model Context Protocol (MCP) to make pet data accessible to other local AI tools.
- **Multimodal Support:** Enhance text instructions with visual references (Agent $\rightarrow$ Sitter).

## 3. System Architecture

### 3.1 The "Brain" (Core Logic)
- **LLM Integration:** Communicates with a local endpoint (e.g., `/v1/chat/completions`).
- **RAG Engine (Retrieval-Augmented Generation):** Uses a vector database to search through unstructured text instructions (Markdown/Text).
- **State Management:** A structured database to track schedules, completed tasks, and item locations.

### 3.2 The "Nervous System" (Interfaces)
- **Discord Bot:** The primary conversational interface for the sitter. Supports natural language queries and command-based logging (e.g., `/fed`).
- **Web Dashboard:**
    - **Owner View:** Management UI for instructions, schedules, and media.
    - **Sitter View:** A high-level daily checklist and emergency contact dashboard.
- **MCP Server:** A standardized interface allowing any MCP-compatible client to query the pet agent's knowledge and tools.

### 3.3 The "Memory" (Storage)
- **SQLite:** Stores structured data (schedules, logs, item metadata, media paths).
- **Vector Database (e.g., ChromaDB):** Stores embeddings of text-based instructions for RAG.
- **Local Filesystem:** Stores multimedia (images/videos) used for visual references.

## 4. Technical Stack
- **Language:** Python
- **API Framework:** FastAPI
- **AI Orchestration:** LangChain or LlamaIndex
- **Database:** SQLite (Relational), ChromaDB (Vector)
- **Discord Integration:** `discord.py`
- **Protocol:** Model Context Protocol (MCP)
- **Frontend:** Streamlit (for rapid dashboard prototyping)

## 5. Development Roadmap

### Phase 1: Core Intelligence (The Brain)
- [ ] Define SQLite database schema (Schedules, Logs, Items, Media).
- [ ] Implement RAG pipeline for text-based instructions.
- [ ] Create the core logic engine to bridge LLM, RAG, and SQLite.
- [ ] Build basic CLI to test "Brain" functionality.

### Phase 2: Primary Interfaces (The Face)
- [ ] **Discord Bot:**
    - [ ] Implement natural language query handling.
    - [ ] Implement command-based logging (e.g., `/fed`, `/meds`).
- [ ] **Web Dashboard:**
    - [ ] Implement Owner UI for instruction management.
    - [ ] Implement Sitter UI for daily task checklists.

### Phase 3: Extensibility (The MCP Layer)
- [ ] Implement MCP Server wrapper around core logic.
- [ ] Expose `search_items`, `get_instructions`, and `log_event` as MCP tools/resources.
- [ ] Verify integration with an MCP client (e.g., Claude Desktop).

### Phase 4: Multimedia (Visual References)
- [ ] Implement media management in the Web Dashboard (upload/link).
- [ ] Enhance agent responses to include image/video paths from the database.

### Phase 5: Vision (The "Nice-to-Have")
- [ ] Integrate a local Vision-Language Model (VLM) for sitter-provided image analysis.

## 6. Data Model Draft (Initial Thoughts)

### `schedules` table
- `id` (PK)
- `task_name` (e.g., "Feeding")
- `pet_id` (FK)
- `scheduled_time` (Time)
- `frequency` (e.g., "daily", "every 12h")

### `activity_logs` table
- `id` (PK)
- `task_id` (FK)
- `timestamp` (DateTime)
- `status` (e.g., "completed", "missed")
- `notes` (Text)

### `knowledge_items` table
- `id` (PK)
- `query_keyword` (Text)
- `description` (Text)
- `media_path` (String/Path)
- `category` (e.g., "location", "instruction", "emergency")
