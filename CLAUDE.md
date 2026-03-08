# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**snx** is a multi-agent orchestration system that spawns teams of Claude Code instances, each running as an A2A (Agent-to-Agent) server. Agents communicate via JSON-RPC over HTTP and can be monitored through a Textual TUI dashboard.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run a team with TUI dashboard (primary usage)
python3 misc/run_team_tui.py samples/team

# Run a team without TUI
python3 misc/run_team.py samples/team

# Interactive A2A client (connect to running agents)
python3 misc/a2a_client.py samples/team

# Lint and type check
ruff check .
mypy cc_team/

# Run tests
pytest

# Clean caches
make clean
```

## Architecture

### Core Package (`cc_team/`)

Four classes work together in a pipeline:

1. **`TeamManager`** (`team_manager.py`) — Parses team directory: reads `config.yml` + `CLAUDE.md` files, creates `AgentConfig` objects, validates setup (port conflicts, missing definitions)

2. **`AgentConfig`** — Dataclass holding name, directory, host/port, and agent definition (CLAUDE.md content)

3. **`AgentProcess`** (`agent_spawner.py`) — Manages a single agent: wraps `InlineAgentExecutor` (Claude SDK + A2A handler), runs Uvicorn HTTP server, handles start/stop/status

4. **`AgentSpawner`** (`agent_spawner.py`) — Orchestrates all `AgentProcess` instances for team-wide startup/shutdown

### `InlineAgentExecutor` (inside `agent_spawner.py`)

The A2A request handler that:
- Creates a `ClaudeSDKClient` with custom tools (`get_agent_info`, `get_team_members`)
- Processes incoming A2A JSON-RPC requests
- Uses `MessageCapture` middleware to log all HTTP traffic

### `MessageCapture` (`message_capture.py`)

Singleton that intercepts all HTTP traffic via Starlette middleware. Classifies messages by type (USER_INPUT, AGENT_RESPONSE, AGENT_TO_AGENT, etc.) and stores up to 10k messages. The TUI reads from this to populate agent panels.

### TUI (`tui.py`)

Textual app with per-agent `AgentPanel` widgets. Bindings: `q` quit, `s` scroll agent list, arrows navigate. Includes message deduplication and timestamp filtering.

## Team Directory Structure

```
my-team/
├── config.yml          # Agent network config (host, port, description per agent)
├── agent-name/
│   ├── CLAUDE.md       # Agent persona/system prompt
│   └── .claude/        # Agent state/settings
└── ...
```

`config.yml` example:
```yaml
team:
  name: "My Team"
agents:
  tom:
    host: localhost
    port: 8001
settings:
  auto_increment_ports: true
```

## Key Integration Points

- **Claude Agent SDK**: Used via `ClaudeSDKClient` for persistent sessions per agent. See `docs/python.md` for full API reference and `misc/` for usage examples.
- **A2A Protocol**: Each agent exposes a JSON-RPC endpoint. The `a2a-sdk` handles protocol details; `InlineAgentExecutor` implements the handler.
- **Environment**: Requires `ANTHROPIC_API_KEY` in environment (see `.env.example`).
