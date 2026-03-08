# Claude Code Team System - Usage Guide

## Quick Start

### 1. Create Your Team Structure
```
team/
├── config.yml              # Central configuration
├── agent1/
│   ├── .claude/
│   └── CLAUDE.md           # Agent personality
├── agent2/
│   ├── .claude/
│   └── CLAUDE.md
└── ...
```

### 2. Configure Your Team
Edit `team/config.yml`:
```yaml
team:
  name: "My Team"
  description: "My awesome AI team"

agents:
  agent1:
    host: localhost
    port: 8001
    description: "Agent 1 role"
  agent2:
    host: localhost
    port: 8002
    description: "Agent 2 role"

settings:
  default_host: localhost
  base_port: 8001
  auto_increment_ports: true
```

### 3. Define Agent Personalities
Each agent needs a `CLAUDE.md` file with their personality, skills, and role.

### 4. Install as CLI Tool
```bash
# From the cc-team source directory
uv pip install -e .
```

### 5. Run Your Team

#### Option A: Initialize New Team
```bash
cc-team my-team --init
cc-team my-team --add-agent agent1
cc-team my-team --add-agent agent2
```

#### Option B: Run Team with Dashboard
```bash
cc-team my-team
```

#### Option C: Individual Agent
```bash
.venv/bin/python dynamic_agent.py my-team/agent1
```

#### Option D: Test System
```bash
.venv/bin/python test_team.py          # Test parsing
.venv/bin/python test_full_team.py     # Test full system
```

## Features

- ✅ **Dynamic Configuration**: Central config.yml for all agents
- ✅ **Agent Personalities**: CLAUDE.md files define each agent
- ✅ **A2A Protocol**: Agents communicate via standard protocol
- ✅ **Textual Dashboard**: Interactive team management UI
- ✅ **Auto Port Management**: Automatic port assignment
- ✅ **Process Management**: Start/stop/restart agents

## Dashboard Controls

- **q**: Quit dashboard
- **r**: Refresh status
- **m**: Send message to selected agent
- **s**: Start selected agent
- **x**: Stop selected agent
- **Arrow keys**: Navigate agent list
- **Enter**: Select agent

## A2A Communication

Agents communicate using JSON-RPC 2.0:
```bash
curl -X POST http://localhost:8001/ \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test",
        "role": "user", 
        "parts": [{"text": "Hello!"}]
      }
    }
  }'
```

## Agent Cards

Get agent information:
```bash
curl http://localhost:8001/.well-known/agent.json
```

## Troubleshooting

### Port Conflicts
- Ensure ports in config.yml are unique
- Use `auto_increment_ports: true` for automatic assignment

### Agent Won't Start
- Check agent directory structure
- Verify CLAUDE.md exists
- Check config.yml syntax

### Communication Issues
- Wait a few seconds after starting agents
- Verify agent is running on correct port
- Check firewall settings

## Example Teams

### 1. Demo Team (samples/team)
A complete example team with:
- **Tom** (port 8001): Technical specialist
- **Jerry** (port 8002): Research analyst  
- **Alice** (port 8003): Project manager

Try it with:
```bash
cc-team samples/team
```

### 2. Template Team (samples/my-new-team)
A basic template team showing:
- Central config.yml structure
- Developer agent with template CLAUDE.md
- Ready for customization

Use as a starting point for your own teams.
