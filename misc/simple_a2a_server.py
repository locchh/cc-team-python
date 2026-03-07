import os
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.utils import new_agent_text_message
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import tool, create_sdk_mcp_server


class SimpleAgentExecutor(AgentExecutor):
    """Simple A2A agent using Claude SDK for intelligent responses"""

    _ = load_dotenv()

    def __init__(self) -> None:
        self.claude_client = None
        self.setup_complete = False

    async def setup_claude(self):
        """Setup Claude SDK with custom tools"""
        if self.setup_complete:
            return
            
        @tool("get_agent_info", "Get information about this agent", {})
        async def get_agent_info(args):
            return {
                "content": [{
                    "type": "text",
                    "text": "I am SimpleA2A, an AI agent powered by Claude SDK. "
                           "I can help with various tasks including conversation, "
                           "analysis, and problem-solving."
                }]
            }

        @tool("calculate", "Simple calculator", {"expression": str})
        async def calculate(args):
            try:
                expression = args.get("expression", "")
                result = eval(expression)  # Simple calculator - be careful with eval!
                return {
                    "content": [{
                        "type": "text",
                        "text": f"{expression} = {result}"
                    }]
                }
            except Exception as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Calculation error: {e}"
                    }]
                }

        # Create MCP server with tools
        server = create_sdk_mcp_server(
            name="simple-agent-tools",
            version="1.0.0",
            tools=[get_agent_info, calculate]
        )

        # Configure Claude SDK
        options = ClaudeAgentOptions(
            model="claude-haiku-4-5",
            mcp_servers={"tools": server},
            allowed_tools=["mcp__tools__get_agent_info", "mcp__tools__calculate"],
            system_prompt="You are SimpleA2A, a helpful AI assistant. "
                         "You have access to calculator tools and can provide "
                         "information about yourself. Be helpful and concise."
        )

        self.claude_client = ClaudeSDKClient(options=options)
        self.setup_complete = True

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute agent task using Claude SDK"""
        if not self.setup_complete:
            await self.setup_claude()

        prompt = context.get_user_input()
        
        # Process with Claude
        async with self.claude_client:
            await self.claude_client.query(prompt)
            
            response_text = ""
            async for msg in self.claude_client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response_text += block.text

        await event_queue.enqueue_event(new_agent_text_message(response_text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation"""
        pass


def main() -> None:
    PORT = int(os.environ.get("SIMPLE_AGENT_PORT", 9999))
    HOST = os.environ.get("AGENT_HOST", "localhost")

    skill = AgentSkill(
        id="general_assistant",
        name="General Assistant",
        description="A helpful AI assistant for various tasks and conversations",
        tags=["assistant", "conversation", "help"],
        examples=[
            "Hello, can you help me?",
            "What can you do?",
            "Calculate 25 * 4",
            "Tell me about yourself"
        ],
    )

    agent_card = AgentCard(
        name="SimpleA2A",
        description="A simple A2A-compliant agent powered by Claude SDK",
        url=f"http://{HOST}:{PORT}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=SimpleAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print(f"🤖 Starting Simple A2A Agent...")
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print(f"📋 Agent Card: http://{HOST}:{PORT}/.well-known/agent.json")
    print(f"💡 Try: curl -X POST http://{HOST}:{PORT}/message:send -H 'Content-Type: application/json' -d '{{\"message\": {{\"parts\": [{{\"text\": \"Hello!\"}}]}}}}'")

    uvicorn.run(server.build(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
