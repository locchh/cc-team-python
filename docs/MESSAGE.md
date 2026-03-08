# Agent Message Capture System

## Why We Need This

### The Problem
When running multiple AI agents that communicate via the A2A protocol, we face a critical visibility gap:

```
          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
          │   Tom AI     │      │   Jerry AI   │      │   Alice AI   │
          │   Agent      │      │   Agent      │      │   Agent      │
          └────────┬─────┘      └────────┬─────┘      └────────┬─────┘
                   │                     │                     │
                   └─────────────────────┼─────────────────────┘
                                         │
                    ┏━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━┓
                    ┃   ??? MYSTERIOUS   │   BLACK BOX ???    ┃
                    ┃    (No Visibility) │                   ┃
                    ┗━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━┛
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          │                              │                              │
    ┌─────▼──────┐              ┌────────▼─────┐              ┌────────▼─────┐
    │   User     │              │   Debug      │              │   Monitor    │
    │  "What are │              │  "Why are    │              │  "How busy   │
    │   they     │              │   they       │              │   are they?  │
    │  talking?" │              │  failing?"   │              │              │
    └────────────┘              └──────────────┘              └──────────────┘
```

**Without message capture, we're flying blind:**
- ❌ No visibility into agent conversations
- ❌ Impossible to debug communication failures
- ❌ No way to monitor system performance
- ❌ Can't analyze agent collaboration patterns

### The Solution
Intercept HTTP communication at the middleware level to capture, store, and analyze all agent interactions:

```
          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
          │   Tom AI     │      │   Jerry AI   │      │   Alice AI   │
          │   Agent      │      │   Agent      │      │   Agent      │
          └────────┬─────┘      └────────┬─────┘      └────────┬─────┘
                   │                     │                     │
                   └──────┬──────────────┼──────────────┬───────┘
                          │              │              │
                 ┌────────▼────┐  ┌──────▼──────┐  ┌───▼────────┐
                 │   HTTP      │  │    HTTP     │  │   HTTP     │
                 │ Middleware  │  │ Middleware  │  │Middleware  │
                 │   (Tom)     │  │  (Jerry)    │  │  (Alice)   │
                 └────────┬────┘  └──────┬──────┘  └───┬────────┘
                          │              │              │
                          └──────────────┼──────────────┘
                                         │
                     ┌────────────────────▼─────────────────────┐
                     │      MessageCapture (CENTRAL HUB)        │
                     │         Stores All Messages              │
                     └────────────────────┬─────────────────────┘
                                         │
            ┌────────────────────────────┼────────────────────────┐
            │                            │                        │
      ┌─────▼──────┐            ┌────────▼────────┐        ┌──────▼─────┐
      │   Debug    │            │    Monitor      │        │  Analyze   │
      │            │            │                │        │            │
      │ See exact  │            │ Real-time      │        │ Patterns & │
      │ flow of    │            │ activity       │        │ statistics │
      │ messages   │            │ dashboard      │        │            │
      └────────────┘            └─────────────────┘        └────────────┘
```

## How It Works: The Mechanism

### 1. HTTP Interception Pattern

We use Starlette middleware to intercept every HTTP request/response:

```
    REQUEST PHASE                  RESPONSE PHASE

┌──────────────┐               ┌──────────────────────┐
│   Client     │               │   Agent Handler      │
│   Request    │               │   (processes logic)  │
└────────┬─────┘               └──────────┬───────────┘
         │                                │
         │  1. REQUEST CAPTURED           │
         ├─────────────────────────────────▶
         │                                │
         │                  2. FORWARDED TO AGENT
         │                                │
         │◀─────────────────────────────────
         │                  3. RESPONSE RECEIVED
         │                                │
         │  4. RESPONSE CAPTURED          │
         │                                │
         ▼                                ▼
┌──────────────┐               ┌──────────────────────┐
│   Client     │               │  MessageCapture      │
│   Response   │               │  (All data stored)   │
└──────────────┘               └──────────────────────┘
```

### 2. Message Classification Logic

The middleware categorizes traffic based on patterns:

```
                        ┌──────────────────┐
                        │   HTTP Request   │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          ┌──────▼──────┐  ┌──────▼──────┐  ┌──▼────────┐
          │   A2A/JSON  │  │  Health     │  │  Generic  │
          │   RPC Call  │  │  Check      │  │   HTTP    │
          └──────┬──────┘  └──────┬──────┘  └────┬──────┘
                 │                │              │
          ┌──────▼──────┐   ┌─────▼─────┐       │
          │  Agent-to-  │   │   System  │       │
          │   Agent     │   │   Event   │       │
          │  (A2A Type) │   │           │       │
          └─────────────┘   └───────────┘       │
                                                 │
                                          ┌──────▼─────┐
                                          │ HTTP Req   │
                                          │ (Default)  │
                                          └────────────┘
```

### 3. Storage Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                  MessageCapture Instance (Singleton)              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  MESSAGE QUEUE: List[CapturedMessage]                       │ │
│  │                                                             │ │
│  │  [001: tom] [002: jerry] [003: alice] ... [N: tom]        │ │
│  │   A2A msg    HTTP req    System evt      A2A resp        │ │
│  │   incoming   outgoing    health check    outgoing        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  THREAD SAFETY: asyncio.Lock()                             │ │
│  │                                                             │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │ │
│  │  │ Thread  │  │ Thread  │  │ Thread  │                  │ │
│  │  │   #1    │  │   #2    │  │   #3    │                  │ │
│  │  └────┬────┘  └────┬────┘  └────┬────┘                  │ │
│  │       │            │            │                        │ │
│  │       └────────────┼────────────┘                        │ │
│  │                    │ (synchronized)                      │ │
│  │            ┌───────▼───────┐                             │ │
│  │            │  Lock Acquired│───▶ Append Message         │ │
│  │            │  Lock Released│                             │ │
│  │            └───────────────┘                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  MEMORY MANAGEMENT                                          │ │
│  │                                                             │ │
│  │  MAX_MESSAGES = 10,000                                    │ │
│  │  If length exceeds limit:                                │ │
│  │    messages.pop(0)  ← Remove oldest message              │ │
│  │    memory_freed += message_size                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### 4. Agent Identification System

Each middleware instance knows its agent:

```
          AGENT SPAWNER
    ┌─────────────────────────────┐
    │                             │
    │  ┌──────┐  ┌──────┐  ┌──────┐
    │  │ Tom  │  │Jerry │  │Alice │
    │  │Config│  │Config│  │Config│
    │  └──┬───┘  └──┬───┘  └──┬───┘
    │     │         │         │
    └─────┼─────────┼─────────┼────────────────────────────┐
          │         │         │
      ┌───▼──┐  ┌───▼──┐  ┌───▼──┐
      │Tom   │  │Jerry │  │Alice │
      │Mware │  │Mware │  │Mware │
      │agent │  │agent │  │agent │
      │="tom"│  │="jerry"│  │="alice"│
      └──┬───┘  └──┬───┘  └──┬───┘
         │         │         │
         └─────────┼─────────┘
                   │
          ┌────────▼──────────┐
          │  MessageCapture   │
          │  (Shared Instance)│
          └───────────────────┘

CAPTURED MESSAGE STRUCTURE:

┌─────────────────────────────────────────────────┐
│  CapturedMessage                                │
│  ┌──────────────────────────────────────────┐  │
│  │ agent_name: "tom"              ← Agent   │  │
│  │ direction: "incoming"          ← Flow    │  │
│  │ message_type: "A2A"            ← Type    │  │
│  │ content: "{jsonrpc...}"        ← Data    │  │
│  │ timestamp: 1709862615          ← When    │  │
│  │ message_id: "msg_12345"        ← ID      │  │
│  │ metadata: {source, size, ...}  ← Extra   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Design Rationale: Why This Architecture?

### 1. HTTP-Level Interception

**Why not A2A-level parsing?**

```
HTTP-LEVEL APPROACH (OUR CHOICE):

  ADVANTAGES                    DISADVANTAGES
  ┌──────────────────┐          ┌──────────────────┐
  │ ✓ Protocol agnostic         │ ✗ Can't parse    │
  │ ✓ Captures ALL comms        │   A2A role field │
  │ ✓ No A2A SDK needed         │ ✗ Limited A2A    │
  │ ✓ Works with any HTTP agent │   understanding  │
  │ ✓ Simple deployment         │ ✗ More pattern   │
  │ ✓ Universal compatibility   │   matching       │
  └──────────────────┘          └──────────────────┘

  Trade-off: Deep understanding for universal compatibility ✓
```

**Trade-off:** We sacrifice deep message understanding for universal compatibility.

### 2. Shared Storage Pattern

**Why not separate storage per agent?**

```
SHARED STORAGE (CHOSEN)          SEPARATE STORAGE (ALTERNATIVE)

┌──────────────────────┐         ┌──────────────────────┐
│ ✓ Single query point │         │ ✓ Isolated failures  │
│ ✓ Cross-agent view   │         │ ✓ Per-agent limits   │
│ ✓ Memory efficient   │         │ ✗ Complex queries    │
│ ✓ Global stats       │         │ ✗ Memory overhead    │
│ ✗ Single failure     │         │ ✗ No cross-view      │
└──────────────────────┘         └──────────────────────┘

Trade-off: Single point of failure for simplicity & visibility ✓
```

**Trade-off:** We accept a single point of failure for simplicity and cross-agent visibility.

### 3. Middleware Per Agent

**Why not one global middleware?**

```
PER-AGENT MIDDLEWARE (CHOSEN)    GLOBAL MIDDLEWARE (ALTERNATIVE)

┌──────────────────────┐         ┌──────────────────────┐
│ ✓ Clear ID per agent │         │ ✓ Single instance    │
│ ✓ Independent life   │         │ ✗ Complex detection  │
│ ✓ Easy per-debugging │         │ ✗ Harder to debug    │
│ ✓ Isolation          │         │ ✗ Tangled code       │
│ ✗ Multiple instances │         │ ✗ Tight coupling     │
└──────────────────────┘         └──────────────────────┘

Trade-off: Multiple instances for clean identification ✓
```

**Trade-off:** We accept multiple instances for clean agent identification.

## Real-World Usage Scenarios

### Scenario 1: Debugging Communication Failures

```
PROBLEM: "Agents aren't talking to each other"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BEFORE MESSAGE CAPTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────┐        ┌──────────────────┐
  │    Tom AI Agent  │        │  Jerry AI Agent  │
  │   "Hello?"       │───────▶│   (silence)      │
  │   (sent or not?) │        │   (received or?) │
  └──────────────────┘        └──────────────────┘

  ❌ No visibility - Did Tom send? Did Jerry receive? Unknown.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AFTER MESSAGE CAPTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────┐        ┌──────────────────┐
  │    Tom AI Agent  │        │  Jerry AI Agent  │
  │   "Hello?"       │───────▶│   "Hi!"          │
  │   ✓ sent        │        │   ✓ received     │
  └─────────┬────────┘        └────────┬─────────┘
            │                          │
            └──────────────┬───────────┘
                           │
            ┌──────────────▼──────────────┐
            │   MESSAGE CAPTURE LOG       │
            ├────────────────────────────┤
            │ 14:30:15  tom → "Hello?"   │
            │ 14:30:16  jerry ← "Hello?" │
            │ 14:30:17  jerry → "Hi!"    │
            │ 14:30:18  tom ← "Hi!"      │
            └────────────────────────────┘

  ✅ Full visibility - Complete conversation flow captured!
```

### Scenario 2: Performance Monitoring

```
PROBLEM: "System is slow - which agent is the bottleneck?"

CAPTURED METRICS ANALYSIS:
┌──────────────────────────────────────────────────────┐
│            AGENT PERFORMANCE STATISTICS              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Tom      ████░░░░░░░░░░░  ~200ms  (50 requests)   │
│  Jerry    ████████████░░░░  ~1.2s   (30 requests)   │ ⚠️  BOTTLENECK
│  Alice    ███░░░░░░░░░░░░░  ~150ms  (25 requests)   │
│                                                      │
│  Finding: Jerry's A2A latency is 6x higher!        │
│  Root: Middleware processing delay identified      │
│                                                      │
└──────────────────────────────────────────────────────┘

ACTIONABLE INSIGHT:
  → Optimize Jerry's request handler
  → Add caching for repeated A2A calls
  → Consider load balancing
```

### Scenario 3: Conversation Analysis

```
PROBLEM: "What are my agents actually working on?"

COLLABORATION PATTERN ANALYSIS:
┌─────────────────────────────────────────────────┐
│     MESSAGE FLOW & AGENT ROLES                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Tom → Jerry    "Data analysis request"        │
│       ▼                                         │
│  Jerry → Tom    "Processed: [results]"         │
│       ▼                                         │
│  Tom → Alice    "Review these results"         │
│       ▼                                         │
│  Alice → Tom    "Validation: ✓ approved"       │
│       ▼                                         │
│  Tom → (User)   "Ready for deployment"         │
│                                                 │
│  ROLE ANALYSIS:                                │
│  • Tom:   Orchestrator (coordinates workflow)  │
│  • Jerry: Processor (analyzes data)            │
│  • Alice: Validator (reviews & approves)       │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Current Limitations & Future Evolution

### Current Constraints

```
┌──────────────────────────────────────────────────────┐
│         KNOWN LIMITATIONS (BY CATEGORY)              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  HTTP-LEVEL CONSTRAINTS:                            │
│  ├─ ✗ Can't parse A2A role field                   │
│  ├─ ✗ User vs AI input indistinguishable            │
│  └─ ✗ HTTP transport only (no WebSocket)            │
│                                                      │
│  STORAGE CONSTRAINTS:                               │
│  ├─ ✗ In-memory only (lost on restart)             │
│  ├─ ✗ No persistent storage layer                   │
│  └─ ✗ Fixed 10,000 message limit                    │
│                                                      │
│  MONITORING CONSTRAINTS:                             │
│  ├─ ✗ No real-time streaming to clients             │
│  ├─ ✗ No alerting/anomaly detection                 │
│  └─ ✗ No dashboard or UI visualization             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Evolution Roadmap

```
PHASE 1: HTTP Capture (CURRENT) ✓ SHIPPED
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ✓ Basic HTTP interception              ┃
┃ ✓ Agent identification                 ┃
┃ ✓ Message classification               ┃
┃ ✓ In-memory storage                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                    ▼
PHASE 2: Deep Analysis (NEXT)
┌────────────────────────────────────────┐
│ ⟲ A2A message body parsing             │
│ ⟲ User vs AI detection                 │
│ ⟲ Intent extraction                    │
│ ⟲ Content analysis & indexing          │
└────────────────────────────────────────┘
                    ▼
PHASE 3: Persistence & Streaming
┌────────────────────────────────────────┐
│ ⟲ SQL/NoSQL database storage           │
│ ⟲ Real-time WebSocket streaming        │
│ ⟲ Message replay & audit trail         │
│ ⟲ Historical trend analysis            │
└────────────────────────────────────────┘
                    ▼
PHASE 4: Intelligence & Observability
┌────────────────────────────────────────┐
│ ⟲ Web dashboard & visualizations       │
│ ⟲ Anomaly detection & alerts           │
│ ⟲ Performance profiling                │
│ ⟲ Agent behavior analytics             │
└────────────────────────────────────────┘
```

## Implementation Summary

This system solves the fundamental visibility problem in multi-agent systems by:

1. **Intercepting** all HTTP communication at the middleware level
2. **Classifying** messages based on patterns and protocols  
3. **Storing** messages in a centralized, thread-safe location
4. **Tagging** each message with agent identification
5. **Providing** query and analysis capabilities

The result is **complete visibility** into agent communication, enabling debugging, monitoring, and optimization of multi-agent systems that were previously opaque black boxes.