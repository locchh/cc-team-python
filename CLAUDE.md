# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**cc-team** is a multi-agent orchestration system that spawns teams of Claude Code instances, each running as an A2A (Agent-to-Agent) server. Agents communicate via JSON-RPC over HTTP and can be monitored through a Textual TUI dashboard.

## Commands

```bash
# Install
uv pip install -e .

# CLI
cc-team run samples/team
cc-team validate samples/team
cc-team help

# Run directly from GitHub
uvx --from git+https://github.com/locchh/snx cc-team run /path/to/team

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

2. **`AgentConfig`** — Dataclass holding name, directory, host/port, model, and agent definition (CLAUDE.md content)

3. **`AgentProcess`** (`agent_spawner.py`) — Manages a single agent: wraps `InlineAgentExecutor` (Claude SDK + A2A handler), runs Uvicorn HTTP server, handles start/stop/status

4. **`AgentSpawner`** (`agent_spawner.py`) — Orchestrates all `AgentProcess` instances for team-wide startup/shutdown

### `InlineAgentExecutor` (inside `agent_spawner.py`)

The A2A request handler that creates a `ClaudeSDKClient` with custom tools (`get_agent_info`, `get_team_members`), processes A2A JSON-RPC requests, and logs traffic via `MessageCapture`.

### `MessageCapture` (`message_capture.py`)

Singleton intercepting all HTTP traffic via Starlette middleware. Stores up to 10k messages; the TUI polls it to populate agent panels.

### TUI (`tui.py`)

Textual app (`TeamTUI`) with per-agent `AgentPanel` widgets. Title shows `CC-Team <session_id>` (unique per run). Panel headers show agent name, port, and model. Bindings: `q` quit, `tab` next panel, `ctrl+a` start all, `ctrl+x` stop all, `s` start focused, `x` stop focused.

### CLI (`cli.py`)

Entry point registered as `cc-team`. Three subcommands: `help`, `validate`, `run`.

## Team Directory Structure

```
my-team/
├── config.yml          # Agent network config (host, port, model, description)
├── agent-name/
│   ├── CLAUDE.md       # Agent persona/system prompt
│   └── .claude/        # Agent state/settings
└── ...
```

`config.yml` model configuration:
```yaml
settings:
  model: claude-sonnet-4-6        # global default
agents:
  tom:
    model: claude-opus-4-6        # per-agent override
```

Available models: `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`, `claude-opus-4-6`

## Key Integration Points

- **Claude Agent SDK**: `ClaudeSDKClient` with `ClaudeAgentOptions(model=...)`. Model flows from `config.yml` → `AgentConfig.model` → `ClaudeAgentOptions`.
- **A2A Protocol**: Each agent exposes a JSON-RPC endpoint. `a2a-sdk` handles protocol; `InlineAgentExecutor` implements the handler.
- **Environment**: Requires `ANTHROPIC_API_KEY` (see `.env.example`).
