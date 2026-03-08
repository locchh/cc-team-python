# Agent Message Capture System

## Why We Need This

### The Problem
When running multiple AI agents that communicate via the A2A protocol, we face a critical visibility gap:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Tom AI    │    │  Jerry AI   │    │  Alice AI   │
│   Agent     │    │   Agent     │    │   Agent     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                    ??? MYSTERIOUS BLACK BOX ???
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
│   User     │    │   Debug    │    │   Monitor   │
│   "What    │    │   "Why     │    │   "How     │
│   are they  │    │   failing?" │    │   busy?"   │
│   talking   │    │            │    │            │
│   about?"   │    │            │    │            │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Without message capture, we're flying blind:**
- ❌ No visibility into agent conversations
- ❌ Impossible to debug communication failures
- ❌ No way to monitor system performance
- ❌ Can't analyze agent collaboration patterns

### The Solution
Intercept HTTP communication at the middleware level to capture, store, and analyze all agent interactions:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Tom AI    │    │  Jerry AI   │    │  Alice AI   │
│   Agent     │    │   Agent     │    │   Agent     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └────────┬─────────┼─────────┬────────┘
                │         │         │
        ┌───────▼─────┐   │   ┌────▼────┐
        │   HTTP      │   │   │  HTTP   │
        │ Middleware  │   │   │Middleware│
        │   (Tom)     │   │   │ (Jerry) │
        └───────┬─────┘   │   └────┬────┘
                │         │         │
                └─────────┼─────────┘
                          │
                ┌─────────▼─────────┐
                │  MessageCapture   │  ← CENTRAL STORAGE
                │   (All Messages)  │
                └─────────┬─────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐
│   Debug      │   │   Monitor    │   │   Analyze    │
│   "See       │   │   "Real-time │   │   "Patterns  │
│   exactly    │   │   activity"  │   │   and stats" │
│   what       │   │             │   │             │
│   happened"  │   │             │   │             │
└──────────────┘   └──────────────┘   └──────────────┘
```

## How It Works: The Mechanism

### 1. HTTP Interception Pattern

We use Starlette middleware to intercept every HTTP request/response:

```
HTTP REQUEST FLOW:

┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Client     │───▶│   Middleware     │───▶│   Agent     │
│   Request    │    │   Intercept      │    │   Handler   │
└─────────────┘    └──────────────────┘    └─────────────┘
       │                      │                      │
       │              1. Capture Request           │
       │              2. Forward to Agent          │
       │                      │                      │
       │              3. Capture Response          │
       │                      │                      │
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Client     │◀───│   Middleware     │◀───│   Agent     │
│   Response   │    │   Intercept      │    │   Handler   │
└─────────────┘    └──────────────────┘    └─────────────┘
```

### 2. Message Classification Logic

The middleware categorizes traffic based on patterns:

```
CLASSIFICATION DECISION TREE:

                    ┌─────────────────┐
                    │  HTTP Request   │
                    └─────────┬───────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
        ┌──────▼────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  A2A/JSON │  │  Health   │  │  Default  │
        │  RPC      │  │  Check    │  │  HTTP     │
        └──────┬────┘  └─────┬─────┘  └─────┬─────┘
               │              │              │
         ┌─────▼─────┐        │              │
         │Agent-to-   │        │              │
         │Agent       │        │              │
         └───────────┘        │              │
                               │              │
                        ┌──────▼─────┐        │
                        │System Event│        │
                        └────────────┘        │
                                               │
                                        ┌──────▼─────┐
                                        │HTTP Request│
                                        └────────────┘
```

### 3. Storage Architecture

```
MEMORY LAYOUT:

┌─────────────────────────────────────────────────────────────┐
│                    MessageCapture Instance                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              messages: List[CapturedMessage]        │  │
│  │                                                     │  │
│  │  [msg_001] [msg_002] [msg_003] ... [msg_N]        │  │
│  │   Tom        Jerry      Alice         ...           │  │
│  │   incoming   outgoing    incoming      ...           │  │
│  │   A2A        HTTP        System        ...           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  Thread Safety                       │  │
│  │                                                     │  │
│  │  asyncio.Lock()  ←───┐                               │  │
│  │                     │                               │  │
│  │  [Thread 1] ────────┼───▶ Capture Message           │  │
│  │  [Thread 2] ────────┼───▶ Capture Message           │  │
│  │  [Thread 3] ────────┘                               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                 Memory Management                    │  │
│  │                                                     │  │
│  │  max_messages: 10,000                               │  │
│  │  if len(messages) > 10,000:                        │  │
│  │      messages.pop(0)  ←─ Remove oldest              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4. Agent Identification System

Each middleware instance knows its agent:

```
AGENT MIDDLEWARE MAPPING:

┌─────────────────────────────────────────────────────────────┐
│                    Agent Spawner                           │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Tom       │  │   Jerry     │  │   Alice     │         │
│  │   Config    │  │   Config    │  │   Config    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
         │                 │                 │                 │
         ▼                 ▼                 ▼                 │
┌────────┼────────┐ ┌─────┼────────┐ ┌─────┼────────┐         │
│ Tom Middleware │ │Jerry Middleware│ │Alice Middleware│         │
│ agent_name="tom"│ │agent_name="jerry"│ │agent_name="alice"│         │
└────────┬────────┘ └─────┬────────┘ └─────┬────────┘         │
         │                 │                 │                 │
         └─────────────────┼─────────────────┘                 │
                           │                                   │
                ┌──────────▼──────────┐                       │
                │  MessageCapture     │                       │
                │  (Shared Instance)  │                       │
                └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

MESSAGE TAGGING:

┌─────────────────────────────────────────────────────────────┐
│                CapturedMessage Structure                    │
│                                                             │
│  agent_name: "tom"          ←─ Which agent?               │
│  direction: "incoming"       ←─ In or Out?                 │
│  message_type: A2A           ←─ What kind?                 │
│  content: "jsonrpc..."      ←─ What was said?             │
│  timestamp: 1234567890      ←─ When?                      │
│  metadata: {...}            ←─ Extra context              │
│  message_id: "msg_123"       ←─ Unique ID                  │
└─────────────────────────────────────────────────────────────┘
```

## Design Rationale: Why This Architecture?

### 1. HTTP-Level Interception

**Why not A2A-level parsing?**

```
PROS OF HTTP LEVEL:
┌─────────────────────────────────────────┐
│ ✓ Protocol Agnostic                    │
│ ✓ Captures ALL communication           │
│ ✓ No A2A SDK dependencies              │
│ ✓ Works with any HTTP-based agent      │
│ ✓ Simple deployment                    │
└─────────────────────────────────────────┘

CONS OF HTTP LEVEL:
┌─────────────────────────────────────────┐
│ ✗ Can't parse A2A message role field   │
│ ✗ Limited message understanding         │
│ ✗ More pattern matching needed          │
└─────────────────────────────────────────┘
```

**Trade-off:** We sacrifice deep message understanding for universal compatibility.

### 2. Shared Storage Pattern

**Why not separate storage per agent?**

```
SHARED STORAGE (OUR CHOICE):
┌─────────────────────────────────────────┐
│ ✓ Single query point                    │
│ ✓ Cross-agent analysis                  │
│ ✓ Memory efficient                      │
│ ✓ Global statistics                     │
│ ✗ Single point of failure              │
└─────────────────────────────────────────┘

SEPARATE STORAGE (ALTERNATIVE):
┌─────────────────────────────────────────┐
│ ✓ Isolated failures                    │
│ ✓ Per-agent memory limits               │
│ ✗ Complex queries                      │
│ ✗ Memory overhead                      │
│ ✗ No cross-agent visibility             │
└─────────────────────────────────────────┘
```

**Trade-off:** We accept a single point of failure for simplicity and cross-agent visibility.

### 3. Middleware Per Agent

**Why not one global middleware?**

```
PER-AGENT MIDDLEWARE (OUR CHOICE):
┌─────────────────────────────────────────┐
│ ✓ Clear agent identification             │
│ ✓ Independent lifecycle                  │
│ ✓ Easy to debug per-agent               │
│ ✗ Multiple middleware instances         │
└─────────────────────────────────────────┘

GLOBAL MIDDLEWARE (ALTERNATIVE):
┌─────────────────────────────────────────┐
│ ✓ Single instance                       │
│ ✗ Complex agent detection logic         │
│ ✗ Harder to debug                       │
└─────────────────────────────────────────┘
```

**Trade-off:** We accept multiple instances for clean agent identification.

## Real-World Usage Scenarios

### Scenario 1: Debugging Communication Failures

```
PROBLEM: "Agents aren't talking to each other"

BEFORE:
┌─────────────┐    ┌─────────────┐
│   Tom AI    │    │  Jerry AI   │
│   "Hello?"  │───▶│   ???       │
│   (no reply)│    │   (silence) │
└─────────────┘    └─────────────┘
❌ What happened? Did Tom send? Did Jerry receive?

AFTER:
┌─────────────┐    ┌─────────────┐
│   Tom AI    │    │  Jerry AI   │
│   "Hello?"  │───▶│   "Hi!"     │
│   (sent)    │    │   (received)│
└──────┬──────┘    └──────┬──────┘
       │                  │
       ▼                  ▼
┌─────────────────────────────────┐
│ Message Capture Log:           │
│ 14:30:15 tom → "Hello?"        │
│ 14:30:16 jerry ← "Hello?"      │
│ 14:30:17 jerry → "Hi!"         │
│ 14:30:18 tom ← "Hi!"           │
└─────────────────────────────────┘
✅ Full visibility into conversation
```

### Scenario 2: Performance Monitoring

```
PROBLEM: "System is slow, which agent is the bottleneck?"

MESSAGE CAPTURE ANALYSIS:
┌─────────────────────────────────────────┐
│ Agent Performance Stats:                │
│                                         │
│ Tom:     avg 200ms  (50 requests)      │
│ Jerry:  avg 1.2s   (30 requests)      │  ← BOTTLENECK!
│ Alice:   avg 150ms  (25 requests)      │
│                                         │
│ Jerry's A2A requests taking 6x longer! │
└─────────────────────────────────────────┘

SOLUTION: Optimize Jerry's A2A handling
```

### Scenario 3: Conversation Analysis

```
PROBLEM: "What are my agents actually working on?"

MESSAGE ANALYSIS:
┌─────────────────────────────────────────┐
│ Agent Collaboration Patterns:           │
│                                         │
│ Tom → Jerry: "Data analysis request"   │
│ Jerry → Tom: "Here's the analysis"     │
│ Tom → Alice: "Review these results"    │
│ Alice → Tom: "Looks good, proceed"     │
│                                         │
│ INSIGHT: Tom is coordinating, Jerry is │
│ analyzing, Alice is reviewing          │
└─────────────────────────────────────────┘
```

## Current Limitations & Future Evolution

### Current Constraints

```
┌─────────────────────────────────────────┐
│ HTTP-LEVEL LIMITATIONS:                 │
│                                         │
│ ✗ Can't parse A2A message role field   │
│ ✗ Don't know user vs AI input          │
│ ✗ Limited to HTTP transport only       │
│                                         │
│ STORAGE LIMITATIONS:                    │
│                                         │
│ ✗ Memory-only (lost on restart)       │
│ ✗ No persistence layer                 │
│ ✗ Fixed 10,000 message limit           │
│                                         │
│ MONITORING LIMITATIONS:                 │
│                                         │
│ ✗ No real-time streaming               │
│ ✗ No alerting system                   │
│ ✗ No dashboard/UI                      │
└─────────────────────────────────────────┘
```

### Evolution Path

```
PHASE 1: HTTP Capture (CURRENT)
┌─────────────────────────────────────────┐
│ ✓ Basic message interception            │
│ ✓ Agent identification                 │
│ ✓ Simple classification                 │
│ ✓ Memory storage                       │
└─────────────────────────────────────────┘
        ↓
PHASE 2: Enhanced Classification
┌─────────────────────────────────────────┐
│ ✓ A2A message parsing                   │
│ ✓ User vs AI detection                  │
│ ✓ Better pattern matching               │
│ ✓ Content analysis                      │
└─────────────────────────────────────────┘
        ↓
PHASE 3: Persistence & Streaming
┌─────────────────────────────────────────┐
│ ✓ Database storage                     │
│ ✓ Real-time WebSocket streaming         │
│ ✓ Message replay                       │
│ ✓ Historical analysis                   │
└─────────────────────────────────────────┘
        ↓
PHASE 4: Advanced Monitoring
┌─────────────────────────────────────────┐
│ ✓ Dashboard UI                         │
│ ✓ Alert system                         │
│ ✓ Performance metrics                  │
│ ✓ Conversation analytics               │
└─────────────────────────────────────────┘
```

## Implementation Summary

This system solves the fundamental visibility problem in multi-agent systems by:

1. **Intercepting** all HTTP communication at the middleware level
2. **Classifying** messages based on patterns and protocols  
3. **Storing** messages in a centralized, thread-safe location
4. **Tagging** each message with agent identification
5. **Providing** query and analysis capabilities

The result is **complete visibility** into agent communication, enabling debugging, monitoring, and optimization of multi-agent systems that were previously opaque black boxes.