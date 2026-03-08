# Claude Code Team System - Architecture

## 📋 Core Classes

Four classes work together to create and manage AI agent teams.

---

## 🧠 **AgentConfig** (`team_manager.py:L12`)

**Purpose**: Data structure for single agent configuration.

**Contains**:
- Agent name and directory
- Host/port settings  
- Agent definition (CLAUDE.md content)
- Network configuration

---

## 🗂️ **TeamManager** (`team_manager.py:L23`)

**Purpose**: Parses team directory and creates `AgentConfig` objects.

**Process**:
```
samples/team/
├── config.yml      ← Central config
├── tom/CLAUDE.md   ← Agent definitions
├── jerry/CLAUDE.md
└── alice/CLAUDE.md
```

1. Reads `config.yml`
2. Scans agent directories
3. Loads `CLAUDE.md` files
4. Creates `AgentConfig` objects
5. Validates setup

---

## 🔄 **AgentProcess** (`agent_spawner.py:L148`)

**Purpose**: Manages single agent lifecycle with inline A2A logic.

**Architecture**:
```
AgentProcess
├── A2A Server (agent logic + Claude SDK)
└── HTTP Server (uvicorn - network transport)
```

**Manages**:
- A2A server creation
- HTTP server lifecycle
- Start/stop operations
- Asyncio task management

---

## 🎯 **AgentSpawner** (`agent_spawner.py:L217`)

**Purpose**: Orchestrates all `AgentProcess` instances.

**Orchestrates**:
- Team startup/shutdown
- Individual agent control
- Status monitoring
- Process management

---

## 🔗 **System Architecture**

### 📊 **System Architecture**

```
┌─────────────┐         ┌─────────────┐
│ TeamManager │────────▶│ AgentConfig │
└──────┬──────┘ creates └─────────────┘
       │
       ▼ passes to
┌─────────────┐
│AgentSpawner │
└──────┬──────┘ 
       │ creates
       ▼
┌─────────────┐
│AgentProcess │
└──────┬──────┘ 
       │ runs
       ▼
┌─────────────┐
│Running A2A  │
│   Agents    │
└─────────────┘
```

### 🔄 **Data Flow**
```
TeamManager parses samples/team/
         ↓
   Creates AgentConfig objects
         ↓
AgentSpawner receives configs
         ↓
Creates AgentProcess instances
         ↓
Each starts A2A + HTTP servers
         ↓
Agents accessible via HTTP API
```

### 🎯 **Class Matrix**

| Class | Role | Input | Output |
|-------|------|-------|--------|
| **AgentConfig** | Data container | - | Configuration data |
| **TeamManager** | Parser | Directory path | AgentConfig objects |
| **AgentProcess** | Process manager | AgentConfig | Running agent |
| **AgentSpawner** | Orchestrator | TeamManager | Team of agents |
