# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Claude Code Team System** is a Python package that orchestrates multi-agent teams where each agent is powered by Claude and communicates via the A2A (Agent-to-Agent) protocol. Each team member can collaborate, delegate tasks, and solve problems together.

## Quick Commands

```bash
# Clean Python cache
make clean

# Run the demo team (3 agents: Tom, Jerry, Alice)
python3 misc/run_team.py samples/team

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest misc/test_a2a_client.py
```

## Architecture Overview

### Four-Layer System

The system orchestrates agents through these key classes:

1. **TeamManager** (`cc_team/team_manager.py`): Parses team directory structure and creates agent configs
   - Scans agent subdirectories (tom/, jerry/, alice/, etc.)
   - Loads CLAUDE.md files (agent personalities)
   - Reads config.yml (central configuration)
   - Returns AgentConfig objects

2. **AgentConfig** (`cc_team/team_manager.py`): Data structure holding per-agent configuration
   - Agent name, directory, host, port
   - Agent definition (personality/system prompt from CLAUDE.md)
   - Network settings

3. **AgentSpawner** (`cc_team/agent_spawner.py`): Orchestrates all agent processes
   - Creates AgentProcess instances for each agent
   - Manages team startup/shutdown
   - Monitors agent health

4. **AgentProcess** (`cc_team/agent_spawner.py`): Manages single agent lifecycle
   - Runs InlineAgentExecutor (A2A server with Claude SDK)
   - HTTP server (uvicorn) for network transport
   - Message capture middleware for observability

### Data Flow

```
Team Directory (e.g., samples/team/)
        ↓
   TeamManager (parses structure)
        ↓
   Creates AgentConfig objects
        ↓
   AgentSpawner (orchestrates)
        ↓
   AgentProcess instances start
        ↓
   Each runs: A2A Server + HTTP Server + MessageCapture Middleware
```

## Team Structure

Team directories follow this structure:

```
samples/team/
├── config.yml              # Central team configuration
├── tom/
│   ├── CLAUDE.md          # Tom's personality (system prompt)
│   └── .claude/           # (optional) Tom's context/memory
├── jerry/
│   ├── CLAUDE.md          # Jerry's personality
│   └── .claude/
└── alice/
    ├── CLAUDE.md          # Alice's personality
    └── .claude/
```

**config.yml** specifies:
- Per-agent: host, port, description
- Global settings: default_host, base_port, auto_increment_ports

**CLAUDE.md** in each agent directory:
- Agent's personality/role definition
- Used as system prompt when Claude processes requests
- Shapes how agent behaves and communicates

## Message Capture System

Every agent runs a message capture middleware that intercepts HTTP communication:

- **Middleware** (`message_capture.py`): HTTP-level message interception
- **Captures**: All A2A calls, health checks, system events
- **Stores**: In global MessageCapture singleton (in-memory, max 10,000 messages)
- **Purpose**: Debug communication, monitor performance, analyze collaboration patterns

The middleware:
- Captures request/response at HTTP level
- Classifies messages (A2A vs health check vs generic HTTP)
- Tags with agent name and direction (incoming/outgoing)
- Thread-safe using asyncio.Lock()

## Key Implementation Details

### Agent Execution (`agent_spawner.py`)

`InlineAgentExecutor` combines:
1. **A2A Server**: Handles agent-to-agent communication (A2A protocol)
2. **Claude SDK Client**: Processes requests using Claude models
3. **Custom Tools**: Two built-in tools: get_agent_info, get_team_members
4. **System Prompt**: Injected from agent's CLAUDE.md + collaboration instructions

### Configuration Loading

- `.claude` directories are created per agent but not required
- CLAUDE.md files are required (validation checks for missing files)
- Port conflicts are detected and reported
- Agents can define custom host/port in config.yml

### Environment

- Loads `.env` file for Claude API credentials (from dotenv)
- Uses claude-agent-sdk for all Claude interactions
- Uses a2a-sdk for A2A protocol handling

## Common Development Tasks

### Adding a New Agent to a Team

1. Create agent subdirectory: `samples/team/myagent/`
2. Create `CLAUDE.md` with agent personality (required)
3. Create `.claude/` directory (optional but recommended)
4. Add agent to `config.yml`:
   ```yaml
   agents:
     myagent:
       host: localhost
       port: 8004
       description: "My agent's description"
   ```

### Running a Custom Team

```bash
python3 misc/run_team.py path/to/your/team
```

### Debugging Agent Communication

The message capture system stores all agent messages. You can:
- Query `get_global_message_capture()` to access stored messages
- Filter by agent_name, direction, message_type, timestamp
- Analyze conversation flow between agents

### Adding Custom Tools to Agents

Modify `InlineAgentExecutor.setup_claude()` in `agent_spawner.py`:
```python
@tool("tool_name", "description", {"param": str})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "result"}]}

server = create_sdk_mcp_server("tools", tools=[my_tool])
# Add tool to options.allowed_tools
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `cc_team/team_manager.py` | Team parsing and agent config discovery |
| `cc_team/agent_spawner.py` | Agent lifecycle and A2A/Claude integration |
| `cc_team/message_capture.py` | HTTP middleware for message interception |
| `misc/run_team.py` | CLI script to run any team directory |
| `samples/team/` | Example team with Tom, Jerry, Alice |
| `docs/ARCHITECTURE.md` | Detailed architecture documentation |
| `docs/MESSAGE.md` | Message capture system design rationale |

## Dependencies

Key packages from `requirements.txt`:
- `claude-agent-sdk`: Claude API integration with multi-turn sessions
- `a2a-sdk[http-server]`: A2A protocol and HTTP server
- `fastapi`, `uvicorn[standard]`: HTTP server framework
- `pyyaml`: Configuration file parsing
- `pytest`, `mypy`, `ruff`: Testing and code quality

## Design Patterns

1. **Singleton MessageCapture**: All agents share one message storage for cross-agent visibility
2. **Per-Agent Middleware**: Each agent's HTTP server has its own middleware instance with agent name
3. **Inline Execution**: Agents run as A2A servers with inline Claude SDK (not subprocesses)
4. **Async/Await**: All operations are async (asyncio-based)
5. **System Prompt Injection**: Agent personality from CLAUDE.md becomes part of system prompt

## Notes for Future Development

- Message capture is Phase 1 (HTTP-level). Phase 2 will add A2A message body parsing
- Current storage is in-memory. Phase 3 plans for persistent database storage
- Team spawning uses local localhost by default. Network configurations possible in config.yml
- Agent definitions (CLAUDE.md) are loaded at startup, not reloaded dynamically
