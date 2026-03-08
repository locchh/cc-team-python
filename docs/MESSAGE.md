# Agent Message Capture System

## Overview

The message capture system intercepts all HTTP communication between agents and stores it for monitoring, debugging, and analysis. It operates at the HTTP middleware level to capture both incoming requests and outgoing responses.

## Architecture

```
User Request → MessageCaptureMiddleware.dispatch() → Agent Handler → Response
                     ↓
                 Captures incoming + outgoing
```

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Tom Agent   │    │ Jerry Agent │    │ Alice Agent │
│ Middleware  │    │ Middleware  │    │ Middleware  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                ┌─────────▼─────────┐
                │  MessageCapture   │  ← SINGLE SHARED INSTANCE
                │   (stores all)     │
                └───────────────────┘
```

## Components

### 1. MessageType (Enum)
Defines the types of messages that can be captured:
- `USER_INPUT` - User input messages (not used at HTTP level)
- `AGENT_RESPONSE` - Agent responses
- `AGENT_TO_AGENT` - A2A protocol messages between agents
- `SYSTEM_EVENT` - Health checks and system events
- `ERROR` - Error messages
- `HTTP_REQUEST` - General HTTP requests
- `HTTP_RESPONSE` - General HTTP responses

### 2. CapturedMessage (Data Container)
Stores individual message data:
```python
@dataclass
class CapturedMessage:
    agent_name: str           # Which agent sent/received
    direction: str            # "incoming" or "outgoing"
    message_type: MessageType  # Type classification
    content: str              # Message content
    timestamp: float          # When captured
    metadata: Dict            # HTTP headers, method, URL, etc.
    message_id: str           # Unique identifier
```

### 3. MessageCapture (Storage System)
Central message storage and retrieval system:
- **Singleton pattern** - One global instance shared by all agents
- **Thread-safe** - Uses asyncio.Lock for concurrent access
- **Memory-limited** - Maintains max_messages limit (default: 10,000)
- **Filterable** - Query by agent, type, direction, time range

### 4. MessageCaptureMiddleware (HTTP Interceptor)
Starlette middleware that intercepts HTTP traffic:
- **Per-agent instances** - Each agent has its own middleware with agent_name
- **Shared storage** - All middleware instances use the same MessageCapture
- **Non-intrusive** - Doesn't block or modify requests
- **Body-safe** - Re-injects request body so handlers can read it

## Message Flow

### 1. Request Interception
```python
async def dispatch(self, request, call_next):
    # 1. Capture incoming request
    request_body = await request.body()
    message_type = self._classify_message(request, request_body)
    
    # 2. Store incoming message
    await self.message_capture.capture(
        agent_name=self.agent_name,  # "tom", "jerry", or "alice"
        direction="incoming",
        message_type=message_type,
        content=request_body,
        metadata={"method": request.method, "url": str(request.url), ...}
    )
```

### 2. Request Processing
```python
    # 3. Pass request to agent handler
    response = await call_next(request)
```

### 3. Response Capture
```python
    # 4. Capture outgoing response
    await self.message_capture.capture(
        agent_name=self.agent_name,
        direction="outgoing",
        message_type=MessageType.AGENT_RESPONSE,
        content=f"[Response: {response.status_code}]",
        metadata={"status_code": response.status_code, "processing_time": ...}
    )
    
    return response
```

## Message Classification

The `_classify_message()` method categorizes incoming requests:

```python
def _classify_message(self, request: Request, body: str) -> MessageType:
    url = str(request.url).lower()
    body_lower = body.lower()
    
    # A2A protocol messages
    if "/a2a" in url or "a2a" in body_lower or "jsonrpc" in body_lower:
        return MessageType.AGENT_TO_AGENT
    
    # System/health endpoints
    if "/health" in url or "/status" in url or "ping" in body_lower:
        return MessageType.SYSTEM_EVENT
    
    # Default HTTP request
    return MessageType.HTTP_REQUEST
```

## Global Instance Management

### Singleton Pattern
```python
_global_message_capture: Optional[MessageCapture] = None

def get_global_message_capture() -> MessageCapture:
    global _global_message_capture
    if _global_message_capture is None:
        _global_message_capture = MessageCapture()  # Create once
    return _global_message_capture  # Always return same instance
```

### Agent Integration
```python
# In agent_spawner.py - each agent gets middleware with shared capture
message_capture = get_global_message_capture()  # Same instance for all agents

app.add_middleware(MessageCaptureMiddleware, 
                   agent_name=config.name,        # "tom", "jerry", "alice"
                   message_capture=message_capture)  # Shared storage
```

## Usage Examples

### Capturing Messages
```python
# Done automatically by middleware
await message_capture.capture("tom", "incoming", MessageType.HTTP_REQUEST, "GET /health")
```

### Retrieving Messages
```python
# Get all messages
all_messages = await message_capture.get_messages()

# Filter by agent
tom_messages = await message_capture.get_messages(agent_name="tom")

# Filter by type
a2a_messages = await message_capture.get_messages(message_type=MessageType.AGENT_TO_AGENT)

# Filter by time range
recent = await message_capture.get_messages(since=time.time() - 3600)

# Limit results
latest_10 = await message_capture.get_messages(limit=10)
```

### Getting Statistics
```python
stats = message_capture.get_stats()
# Returns:
# {
#     "total_messages": 150,
#     "message_count": 150,
#     "agents": ["tom", "jerry", "alice"],
#     "agent_counts": {"tom": 50, "jerry": 50, "alice": 50},
#     "type_counts": {"http_request": 30, "agent_to_agent": 60, "agent_response": 60}
# }
```

## Key Design Decisions

### 1. HTTP-Level Interception
- **Pros**: Captures all communication, protocol-agnostic
- **Cons**: Can't distinguish user vs AI messages (requires A2A-level parsing)

### 2. Shared Storage
- **Pros**: Centralized data, easy querying, memory efficient
- **Cons**: Single point of failure (mitigated by thread safety)

### 3. Middleware Per Agent
- **Pros**: Clear agent identification, independent lifecycle
- **Cons**: Multiple middleware instances (minimal overhead)

### 4. Message Classification
- **Current**: URL and body pattern matching
- **Limitation**: Can't parse A2A message `role` field at HTTP level

## Memory Management

```python
# Automatic cleanup when limit reached
if len(self.messages) > self.max_messages:
    self.messages.pop(0)  # Remove oldest message
```

## Thread Safety

```python
async def capture(self, ...):
    message = CapturedMessage(...)
    
    async with self._lock:  # Prevent race conditions
        self.messages.append(message)
        self._message_count += 1
```

## Limitations

1. **HTTP-level only** - Can't parse A2A message content (role field)
2. **Memory-based** - Messages lost on restart (no persistence)
3. **No real-time notifications** - Subscribers removed (cleaned up)
4. **Body truncation** - Response bodies not fully captured (content-length issues)

## Future Enhancements

1. **A2A-level parsing** - Parse message role field for better classification
2. **Persistence** - Store messages to database/file
3. **Real-time streaming** - WebSocket or SSE for live monitoring
4. **Message filtering** - More sophisticated classification rules
5. **Compression** - Compress large message bodies