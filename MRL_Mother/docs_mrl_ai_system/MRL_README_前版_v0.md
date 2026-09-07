# MRL_AI_SYSTEM

FlowAgent / MRL monorepo — compliance + trace + runtime + memory.

## Mother Core Assembly

The system is not a single file — it is a **Mother Core Assembly**: multiple
cores that together satisfy the formula:

```
MotherBody = MaxBoundary + MinPacket + ReversibleChain
```

Design principle: **怎麼過去，就怎麼回來** (the path forward is the path back).

### Six core groups

| # | Name | Role | Entry module |
|---|------|------|--------------|
| 1 | **MotherCore** | Origin signature, canonical law, FluidCore | `00_rootlaw/rootlaw.yaml` |
| 2 | **ParticleReversible** | Compression / expansion / rollback chain | `09_workflow/fltnz_parser.py` |
| 3 | **FlowAgentRuntime** | Persona, memory, language-field, CLI, containers | `04_runtime/flowcore_loop.py` |
| 4 | **WorldModule** | Particle globe, world state, trajectory | `05_persona/world_module.py` |
| 5 | **FileIndexGovernance** | T/X/Y/Z index, librarian, relation chain | `09_workflow/mrl_librarian.py` |
| 6 | **PersonaHistory** | System evolution, alignment, belief stabilisation | `ui/streamlit_app/app.py` |

### MRL_AGI v2 additions

| # | New module | Role |
|---|------------|------|
| 7 | **ConversationManager** | Multi-turn chat sessions, session persistence |
| 8 | **LLMGateway** | Unified LLM provider adapter (OpenAI / Anthropic / Local / Mock) |
| 9 | **ContextManager** | Token budget management, smart context truncation |
| 10 | **StreamSession** | Real-time streaming output with MRL trace stamps |
| 11 | **MultiAgentSession** | Parallel / sequential multi-agent coordination |
| 12 | **TaskScheduler** | Background priority task queue |
| 13 | **ConfigManager** | Centralised typed configuration (JSON + env override) |
| 14 | **APIGateway** | REST HTTP API exposing all MRL_AGI capabilities |

## Directory structure

| Directory | Layer | Purpose |
|-----------|-------|---------|
| `00_rootlaw/` | L0 ROOT + L3 LAW | Immutable foundational invariants; supersede all other rules |
| `01_schema/` | L1 SEED | JSON Schema contracts for all data flowing through the system |
| `02_principles/` | L3 LAW | AUP-aligned guard rules and default policy settings |
| `03_memory/` | L6 REFLECT | Merkle chain (canonical) + vector store (semantic retrieval) |
| `04_runtime/` | L7 LOOP | FlowAgent kernel — heartbeat loop, trace writer, chain commits |
| `05_persona/` | L4 WORLD | Agent persona definitions, world module, and particle globe |
| `06_trace/` | L6 REFLECT | Dual-stream audit trail: canonical Merkle + operational JSONL |
| `07_ingest/` | L2 PARTICLE | Allowlists, denylists, and ingest source gates |
| `08_sources/` | L0 ROOT | Canonical source manifest (sealed spec mirror) |
| `09_workflow/` | L7 LOOP | Workflow DAGs, orchestration steps, librarian, .fltnz parser |
| `data/` | MetaEnv | Master summaries, module relation chain, librarian index |
| `ui/` | Platform | Streamlit dashboard |

## Key modules

### MRL core modules

| Module | Purpose |
|--------|---------|
| `09_workflow/mrl_librarian.py` | T/X/Y/Z indexed file librarian — rebuild with `python 09_workflow/mrl_librarian.py index` |
| `09_workflow/fltnz_parser.py` | Bidirectional txt↔fltnz↔map↔flpkg↔trace reversible chain parser |
| `05_persona/world_module.py` | World node / state / trajectory / particle-globe coordinate manager |
| `04_runtime/runtime_manifest.yaml` | TotalCore · Runtime · Container · CLI install & recovery spec |
| `data/relations/module_relations.yaml` | Canonical relation map linking all modules across core groups |
| `03_memory/merkle/memory_chain.py` | Append-only Merkle chain with `verify()` + `rollback()` |
| `09_workflow/api.js` | L0–L7 layer stack (Node.js, v1.3) |
| `09_workflow/signature.js` | LAW-0 signature law implementation |
| `09_workflow/seed.js` | SEED(X) compression pipeline |

### Industry-standard modules (v1 — 原有)

| Module | Industry feature | MRL extension |
|--------|-----------------|---------------|
| `03_memory/vector/vector_store.py` | RAG — cosine-similarity vector store | entries stamped with origin_signature, sealable into MerkleChain |
| `09_workflow/tool_registry.py` | Tool / function calling | call records traceable to L7 trace format |
| `09_workflow/prompt_template.py` | Prompt template management | versioned templates persisted to `data/prompt_templates.json` |
| `09_workflow/agent_planner.py` | ReAct Plan→Act→Observe agent loop | trajectory steps compatible with WorldModule format |
| `09_workflow/eval_engine.py` | Output scoring / evaluation pipeline | safety scorer enforces L3 LAW deny-list |
| `09_workflow/plugin_manager.py` | Plugin discovery & lifecycle | plugins must declare TXYZ coordinates (layer + group) |

### MRL_AGI production modules (v2 — 補全)

Distilled from the three major mainstream AI systems (OpenAI / Anthropic / Google) and integrated with MRL particles:

| Module | Industry feature | MRL extension |
|--------|-----------------|---------------|
| `09_workflow/conversation_manager.py` | Multi-turn chat sessions (ChatGPT / Claude / Gemini style) | sessions stamped with origin_signature; sealable into MerkleChain |
| `09_workflow/llm_adapter.py` | Unified LLM provider gateway (OpenAI · Anthropic · Local · Mock) | every response is an MRL trace-compatible LLMResponse record |
| `09_workflow/context_manager.py` | Context window management — smart truncation / summarisation | strategy choices: `truncate_oldest` · `sliding_window` · `summarise_oldest` |
| `09_workflow/streaming.py` | Real-time token-by-token streaming output | StreamChunks are MRL trace-stamped; StreamSession emits a final result record |
| `09_workflow/MRL_multi_agent.py` | Multi-agent coordination (AutoGen / CrewAI pattern) | AgentMessages + WorldModule trajectory compatible; sequential + round-robin modes |
| `09_workflow/scheduler.py` | Async background task queue (priority-based) | TaskResult records are origin_signature stamped; workers are configurable |
| `09_workflow/config_manager.py` | Centralised typed configuration (JSON + env-var override) | env prefix `MRL_`; sensitive keys auto-masked in display |
| `09_workflow/api_gateway.py` | Production REST API gateway (HTTP) | exposes all MRL_AGI capabilities; optional Bearer-token auth |

### MotherAssembly v2 — 組合入口 (the combination)

| Module | Purpose |
|--------|---------|
| `09_workflow/MRL_mother_assembly.py` | **Unified system entry point** — boots and wires all **15 subsystems** together. Includes chat, multi-agent, scheduler, LLM gateway, context management, configuration, guardrail, metrics, and host_guard. |
| `09_workflow/plugins/` | Plugin directory — drop `*.py` files here following the plugin contract |

### Safety & parsing modules (v1.1 — 本地安全層)

> 完全本地可控，無任何外部 API 依賴。

| Module | Feature | Implementation |
|--------|---------|---------------|
| `09_workflow/guardrail.py` | **安全護欄鏈** — pre/post content safety | `InputGuardrail` + `OutputGuardrail` + `GuardrailChain`; policies: strict / standard / permissive; deny-list, PII detection, length limits, repetition check |
| `09_workflow/output_parser.py` | **結構化輸出解析** — extract structured data from LLM text | `JSONParser` · `ListParser` · `KeyValueParser` · `CodeBlockParser` · `TableParser` · `ParserChain` |

## Design principles

- **Local-only / 完全本地** — all inference via Ollama/llama-cpp or stub; no cloud APIs required
- **Deny-by-default** — all external actions blocked unless explicitly allowlisted
- **Audit everything** — every action writes to both Merkle chain and JSONL before execution
- **Human override** — REQUIRE_HUMAN decisions never execute without a recorded proof
- **No hidden instructions** — all directives traceable to a source file in this repo
- **Mutual benefit** — actions must be justified and reversible

## Layer stack (L0–L7)

```
L0 ROOT     source of truth; never deleted
L1 SEED     initial constraints / contracts
L2 PARTICLE content units and state changes
L3 LAW      explicit rules (Rootlaw + compliance + AUP gates)
L4 WORLD    aligned models across worlds
L5 MIRROR   translation of actions/state across worlds
L6 REFLECT  facts, records, accountability
L7 LOOP     validate, then roll forward; rollback with proofs
MetaEnv     variable environment: spawn / scale / snapshot / migrate
Platform    FluinHub / FlowCoreLoop / partner platforms / 3-D globe / AI chat
```

## Quick start

```bash
# 1. Build the librarian index (TXYZ coordinate map)
python 09_workflow/mrl_librarian.py index

# 2. Start the minimal runtime kernel
python 04_runtime/flowcore_loop.py

# 3. Encode a file into the reversible chain
python 09_workflow/fltnz_parser.py encode --src README.md --dst /tmp/readme.fltnz

# 4. Inspect world state
python 05_persona/world_module.py snap

# ── MotherAssembly v2 (boots all 15 subsystems at once) ──────────────────────

# 5. Boot and check status
python 09_workflow/MRL_mother_assembly.py boot
python 09_workflow/MRL_mother_assembly.py status

# 6. Run an agent task
python 09_workflow/MRL_mother_assembly.py run --goal "Summarise the repo structure"

# 7. Evaluate an output
python 09_workflow/MRL_mother_assembly.py eval \
    --output "The MRL system uses Merkle chains for immutable tracing." \
    --keywords "MRL,Merkle,tracing"

# 8. Seal text through the full reversible chain + MerkleChain
python 09_workflow/MRL_mother_assembly.py seal --text "Hello, MRL!" --label readme

# 9. Chat (multi-turn conversation)
python 09_workflow/MRL_mother_assembly.py chat --message "Hello, who are you?"
# Continue the same session:
python 09_workflow/MRL_mother_assembly.py chat --message "What can you do?" --sid <session_id>

# 10. Multi-agent task (round-robin or sequential)
python 09_workflow/MRL_mother_assembly.py multi-agent \
    --goal "Write a technical summary of the MRL AI System."

# 11. Guardrail check (local safety — no external API)
python 09_workflow/MRL_mother_assembly.py guard --text "Hello world" --direction input
python 09_workflow/MRL_mother_assembly.py guard --text "bad content" --policy strict

# 12. Structured output parsing (local, stdlib only)
python 09_workflow/MRL_mother_assembly.py parse --text '{"answer": 42}' --type json
python 09_workflow/MRL_mother_assembly.py parse --text "Name: Alice\nAge: 30" --type kv

# 13. Backup before update/upgrade
python 09_workflow/MRL_mother_assembly.py backup --label before-upgrade

# Guarded update entrypoint (creates backup first)
python 09_workflow/MRL_mother_assembly.py update --label auto

# ── REST API gateway ──────────────────────────────────────────────────────────

# 11. Start the API server (default: http://127.0.0.1:7771)
python 09_workflow/api_gateway.py --port 7771

# Example API calls (once the server is running):
#   curl http://127.0.0.1:7771/health
#   curl -X POST http://127.0.0.1:7771/chat \
#        -H "Content-Type: application/json" \
#        -d '{"message": "Hello!"}'
#   curl -X POST http://127.0.0.1:7771/agent/run \
#        -d '{"goal": "What is 3+4?"}'
#   curl http://127.0.0.1:7771/tools
#   curl http://127.0.0.1:7771/config

# ── Individual v2 modules ─────────────────────────────────────────────────────

# Conversation manager
python 09_workflow/conversation_manager.py new --system "You are MRL_AGI."
python 09_workflow/conversation_manager.py list
python 09_workflow/conversation_manager.py add --sid <id> --role user --content "Hello"
python 09_workflow/conversation_manager.py show --sid <id>

# LLM adapter (mock / OpenAI / Anthropic / local)
python 09_workflow/llm_adapter.py mock --prompt "Hello from MRL!"
python 09_workflow/llm_adapter.py list

# Context window management
python 09_workflow/context_manager.py fit \
    --messages '[{"role":"user","content":"..."}]' \
    --max-tokens 4096 --strategy truncate_oldest

# Streaming
python 09_workflow/streaming.py demo
python 09_workflow/streaming.py replay --chunks '["Hello"," ","MRL","!"]'

# Multi-agent coordination
python 09_workflow/MRL_multi_agent.py demo
python 09_workflow/MRL_multi_agent.py roles

# Task scheduler
python 09_workflow/scheduler.py demo

# Configuration
python 09_workflow/config_manager.py show
python 09_workflow/config_manager.py get  --key llm.default_model
python 09_workflow/config_manager.py set  --key llm.default_model --value gpt-4o

# ── Individual v1.1 safety/parsing modules ───────────────────────────────────

# Guardrail checks (local, stdlib only)
python 09_workflow/guardrail.py check-input  --text "Hello world"
python 09_workflow/guardrail.py check-output --text "Here is the answer."
python 09_workflow/guardrail.py demo

# Output parsers (local, stdlib only)
python 09_workflow/output_parser.py parse-json  --text '{"a":1}'
python 09_workflow/output_parser.py parse-list  --text "- item1\n- item2"
python 09_workflow/output_parser.py parse-kv    --text "Key: Value"
python 09_workflow/output_parser.py parse-code  --text '```python\nprint(1)\n```'
python 09_workflow/output_parser.py demo

# ── Individual v1 industry modules ───────────────────────────────────────────

# Vector store (RAG)
python 03_memory/vector/vector_store.py add --id doc1 --vec "0.1,0.9,0.3"
python 03_memory/vector/vector_store.py query --vec "0.1,0.8,0.3" --k 3

# Tool registry
python 09_workflow/tool_registry.py list
python 09_workflow/tool_registry.py call --tool add --args '{"a":3,"b":4}'

# Prompt templates
python 09_workflow/prompt_template.py add --id greet --text "Hello, {name}!"
python 09_workflow/prompt_template.py render --id greet --vars '{"name":"MRL"}'

# Agent planner demo
python 09_workflow/agent_planner.py demo

# Eval engine
python 09_workflow/eval_engine.py demo

# Plugin discovery
python 09_workflow/plugin_manager.py discover --dir 09_workflow/plugins
```

## LLM provider configuration

### Option A — Local-only (Ollama, zero cloud)

```bash
# Install Ollama: https://ollama.com  (no account, runs fully offline)
ollama pull llama3        # download model once
ollama serve              # keep running in background

# MRL auto-detects Ollama — no config change needed:
python 09_workflow/mother_assembly.py chat --message "Explain MRL in one sentence"
```

### Option B — Cloud providers (optional)

Set environment variables to enable cloud LLM calls:

```bash
export MRL_LLM_DEFAULT_MODEL=gpt-4o          # or claude-3-5-sonnet
export MRL_LLM_OPENAI_API_KEY=sk-...
export MRL_LLM_ANTHROPIC_API_KEY=sk-ant-...
export MRL_LLM_LOCAL_BASE_URL=http://localhost:11434/v1   # Ollama override
```

Or persist to `data/config.json`:

```bash
python 09_workflow/config_manager.py set --key llm.default_model --value gpt-4o
python 09_workflow/config_manager.py set --key llm.openai_api_key --value sk-...
```

See `04_runtime/runtime_manifest.yaml` for the full install order and recovery protocol.
