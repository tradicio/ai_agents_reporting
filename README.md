# Agents reporting for duty! - PyCon 2026

Local LLM inference demo showcasing three agent architectures running against a self-hosted [vLLM](https://github.com/vllm-project/vllm) server.

## Requirements

- Docker with [NVIDIA Container Runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- An NVIDIA GPU
- Python 3.11+

---

## 1. Start the inference server

The `docker-compose.yml` starts two services:

| Service | Description | Port |
|---------|-------------|------|
| `vllm` | OpenAI-compatible inference server — serves `Qwen/Qwen2.5-7B-Instruct-AWQ` with AWQ Marlin quantization | `8000` |
| `open-webui` | Web chat UI connected to vLLM | `3000` |

```bash
# Start both services in the background
docker compose up -d

# Tail logs (wait until vLLM prints "Application startup complete")
docker compose logs -f vllm

# Stop everything
docker compose down
```

Model weights are downloaded on first start and cached in `./model_files/` so subsequent starts are instant.

---

## 2. Python environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the example env file and adjust if needed (defaults match the Docker setup):

```bash
cp .env.example .env
```

`.env` contents:

```
VLLM_BASE_URL = "http://localhost:8000/v1"
VLLM_MODEL    = "Qwen/Qwen2.5-7B-Instruct-AWQ"
```

---

## 3. Running the demo scripts

All scripts load `.env` automatically. Activate the virtual environment first:

```bash
source venv/bin/activate
```

### code_review.py — Reflection agent

Runs a code review task through two agents side-by-side so you can compare their outputs:

- **PlainLLM** — single-turn call, no iteration
- **ReflectionAgent** — agentic loop that emits chain-of-thought via a `reflect` tool, then iterates until it produces a final answer

```bash
python code_review.py
```

### github_assistant.py — ReAct agent

Runs a **ReAct** (Reason + Act) agent that browses open GitHub issues in a repository and lets the model decide when to post comments. Requires two additional environment variables in `.env`:

```
GITHUB_TOKEN = "ghp_..."        # personal access token with repo scope
GITHUB_REPO  = "owner/repo"     # e.g. "acme/my-project"
```

```bash
python github_assistant.py
```

### project_manager.py — Multi-agent orchestrator

Runs a **ProjectManagerAgent** that orchestrates three specialised sub-agents:

| Sub-agent | Role |
|-----------|------|
| `DevAgent` | Writes implementation code |
| `TesterAgent` | Writes pytest tests |
| `DocAgent` | Writes documentation |

The orchestrator delegates subtasks via tool calls and collects results from each sub-agent.

```bash
python project_manager.py
```

---

## Architecture overview

```
src/pycon2026/
├── abstract/
│   ├── agent.py          # Agent ABC — LLM client, prompt loading, FSM, event bus
│   ├── event.py          # Base event class
│   ├── memory.py         # Key-value store per agent instance
│   └── tool.py           # Tool definition helpers
├── agents/
│   ├── plain_llm.py              # Single-turn agent
│   ├── reflection/
│   │   └── reflection_agent.py   # Generate → critique → refine loop
│   ├── react/
│   │   └── github_assistant.py   # ReAct agent with GitHub tools
│   └── multi_agent/
│       ├── project_manager.py    # Orchestrator
│       ├── sub_agents.py         # Dev / Tester / Doc sub-agents
│       └── reflective_sub_agent.py  # Reflect-tool loop with context compression
├── events/               # Typed events emitted by agents
├── tools/                # Tool schemas (Pydantic models)
├── prompts/prompts.yaml  # All system prompts and user-turn templates
├── constants/constants.py
└── utils/
    └── logging_setup.py  # File logging setup per agent run
```

### Adding a new agent

1. Add a new key to `src/pycon2026/prompts/prompts.yaml` with at least a `system` entry.
2. Create a class in `src/pycon2026/agents/` that extends `Agent`. Declare `initial_state` and `transitions` for FSM tracking.
3. Implement `run(self, task: str) -> str`. Call `self.emit(SomeEvent(...))` at each meaningful state transition.
4. Optionally define typed events in `events/` (subclass `Event`) and tool schemas in `tools/` (use the `Tool` Pydantic model).
