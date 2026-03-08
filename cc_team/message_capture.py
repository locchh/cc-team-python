"""
Message Capture System - HTTP level message interception for agent communication
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import starlette.middleware.base
from fastapi import Request


class MessageType(Enum):
    """Types of messages that can be captured"""

    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    AGENT_TO_AGENT = "agent_to_agent"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"
    HTTP_REQUEST = "http_request"
    HTTP_RESPONSE = "http_response"


@dataclass
class CapturedMessage:
    """Represents a captured HTTP message"""

    agent_name: str
    direction: str  # "incoming" or "outgoing"
    message_type: MessageType
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: f"msg_{int(time.time() * 1000000)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "agent_name": self.agent_name,
            "direction": self.direction,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "message_id": self.message_id,
        }


class MessageCapture:
    """Central message capture and storage system"""

    def __init__(self, max_messages: int = 10000):
        self.messages: List[CapturedMessage] = []
        self._lock = asyncio.Lock()
        self.max_messages = max_messages
        self._message_count = 0

    async def capture(
        self,
        agent_name: str,
        direction: str,
        message_type: MessageType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture a message"""
        message = CapturedMessage(
            agent_name=agent_name,
            direction=direction,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
        )

        async with self._lock:
            self.messages.append(message)
            self._message_count += 1

            # Maintain message limit
            if len(self.messages) > self.max_messages:
                self.messages.pop(0)

        return message.message_id

    async def get_messages(
        self,
        agent_name: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        direction: Optional[str] = None,
        since: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[CapturedMessage]:
        """Get messages with optional filtering"""
        async with self._lock:
            messages = list(self.messages)

        # Apply filters
        if agent_name:
            messages = [m for m in messages if m.agent_name == agent_name]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        if direction:
            messages = [m for m in messages if m.direction == direction]

        if since:
            messages = [m for m in messages if m.timestamp >= since]

        # Sort by timestamp (newest first)
        messages.sort(key=lambda m: m.timestamp, reverse=True)

        if limit:
            messages = messages[:limit]

        return messages

    def get_stats(self) -> Dict[str, Any]:
        """Get capture statistics"""
        agent_counts = {}
        type_counts = {}

        for message in self.messages:
            agent_counts[message.agent_name] = (
                agent_counts.get(message.agent_name, 0) + 1
            )
            type_counts[message.message_type.value] = (
                type_counts.get(message.message_type.value, 0) + 1
            )

        return {
            "total_messages": len(self.messages),
            "message_count": self._message_count,
            "agents": list(agent_counts.keys()),
            "agent_counts": agent_counts,
            "type_counts": type_counts,
        }


class MessageCaptureMiddleware(starlette.middleware.base.BaseHTTPMiddleware):
    """Starlette middleware to capture HTTP messages for agent communication"""

    def __init__(self, app, agent_name: str, message_capture: MessageCapture):
        super().__init__(app)
        self.agent_name = agent_name
        self.message_capture = message_capture

    async def dispatch(self, request: Request, call_next):
        """Capture HTTP request and response"""
        start_time = time.time()

        # Capture incoming request body without consuming it.
        # We buffer the raw bytes and re-inject them so downstream
        # handlers can still read the body normally.
        request_body = ""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                raw_body = await request.body()
                request_body = raw_body.decode("utf-8", errors="ignore")

                # Re-inject body so downstream can read it again
                async def receive():
                    return {
                        "type": "http.request",
                        "body": raw_body,
                        "more_body": False,
                    }

                request = Request(request.scope, receive)
        except Exception:
            request_body = "[Failed to read request body]"

        # Determine message type based on request
        message_type = self._classify_message(request, request_body)

        await self.message_capture.capture(
            agent_name=self.agent_name,
            direction="incoming",
            message_type=message_type,
            content=request_body,
            metadata={
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
            },
        )

        # Process request
        response = await call_next(request)

        # Capture outgoing response
        response_body = ""
        try:
            # Don't read response body to avoid content-length issues
            # Just capture basic response info
            response_body = f"[Response: {response.status_code}]"
        except Exception:
            response_body = "[Failed to read response]"

        await self.message_capture.capture(
            agent_name=self.agent_name,
            direction="outgoing",
            message_type=MessageType.AGENT_RESPONSE,
            content=response_body,
            metadata={
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "processing_time": time.time() - start_time,
            },
        )

        return response

    def _classify_message(self, request: Request, body: str) -> MessageType:
        """Classify the type of incoming message"""
        url = str(request.url).lower()
        body_lower = body.lower()

        # Check for A2A protocol messages
        if "/a2a" in url or "a2a" in body_lower or "jsonrpc" in body_lower:
            return MessageType.AGENT_TO_AGENT

        # Check for system/health endpoints
        if "/health" in url or "/status" in url or "ping" in body_lower:
            return MessageType.SYSTEM_EVENT

        # For HTTP requests, we can't reliably distinguish user vs AI input
        # The A2A protocol uses 'role' field in message body, but we're at HTTP level
        # Default to HTTP request
        return MessageType.HTTP_REQUEST


# Global message capture instance
_global_message_capture: Optional[MessageCapture] = None


def get_global_message_capture() -> MessageCapture:
    """Get or create the global message capture instance"""
    global _global_message_capture
    if _global_message_capture is None:
        _global_message_capture = MessageCapture()
    return _global_message_capture


def set_global_message_capture(message_capture: MessageCapture):
    """Set the global message capture instance"""
    global _global_message_capture
    _global_message_capture = message_capture
