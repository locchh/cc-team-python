"""
Dynamic A2A Agent that loads configuration from config.yml
"""
import os
import yaml
import uvicorn
from pathlib import Path
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import tool, create_sdk_mcp_server


class DynamicAgentExecutor(AgentExecutor):
    """Dynamic A2A agent using Claude SDK with configurable personality"""

    _ = load_dotenv()

    def __init__(self, agent_dir: Path, config: dict = None) -> None:
        self.agent_dir = agent_dir
        self.config = config or self.get_default_config()
        self.personality = self.load_personality()
        self.claude_client = None
        self.setup_complete = False

    def get_default_config(self) -> dict:
        """Get default configuration when no config is provided"""
        return {
            'host': 'localhost',
            'port': 8001,
            'agent_name': self.agent_dir.name,
            'description': f'A2A agent: {self.agent_dir.name}'
        }

    def load_personality(self) -> str:
        """Load personality from CLAUDE.md"""
        personality_file = self.agent_dir / "CLAUDE.md"
        if personality_file.exists():
            with open(personality_file, 'r') as f:
                return f.read().strip()
        else:
            return f"You are {self.agent_dir.name}, a helpful AI assistant."

    async def setup_claude(self):
        """Setup Claude SDK with custom tools"""
        if self.setup_complete:
            return
            
        @tool("get_agent_info", "Get information about this agent", {})
        async def get_agent_info(args):
            return {
                "content": [{
                    "type": "text",
                    "text": f"I am {self.config['agent_name']}, an AI agent. {self.config.get('description', '')}"
                }]
            }

        @tool("get_team_members", "Get information about team members", {})
        async def get_team_members(args):
            return {
                "content": [{
                    "type": "text",
                    "text": "I can communicate with other team members via A2A protocol. We work together to solve complex problems."
                }]
            }

        server = create_sdk_mcp_server(
            name=f"{self.config['agent_name']}-tools",
            version="1.0.0",
            tools=[get_agent_info, get_team_members]
        )

        system_prompt = f"{self.personality}\n\nYou are part of a team of AI agents. You can communicate with other team members using the A2A protocol. Be helpful, collaborative, and work together with your team."

        options = ClaudeAgentOptions(
            mcp_servers={"tools": server},
            allowed_tools=["mcp__tools__get_agent_info", "mcp__tools__get_team_members"],
            system_prompt=system_prompt
        )

        self.claude_client = ClaudeSDKClient(options=options)
        self.setup_complete = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute agent task using Claude SDK"""
        if not self.setup_complete:
            await self.setup_claude()

        prompt = context.get_user_input()
        
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


def create_agent_server(agent_dir: Path, config: dict = None):
    """Create A2A server for a specific agent"""
    agent_executor = DynamicAgentExecutor(agent_dir, config)
    config = agent_executor.config

    skill = AgentSkill(
        id="team_collaboration",
        name="Team Collaboration",
        description="AI agent that works with other team members",
        tags=["team", "collaboration", "a2a"],
        examples=[
            "What can you help me with?",
            "Can you work with your team on this?",
            "Tell me about your capabilities"
        ],
    )

    agent_card = AgentCard(
        name=config['agent_name'],
        description=config.get('description', f'A2A agent: {config["agent_name"]}'),
        url=f"http://{config['host']}:{config['port']}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    return server, config


def main():
    """Main function for standalone agent execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dynamic_agent.py <agent_directory>")
        sys.exit(1)
    
    agent_dir = Path(sys.argv[1])
    if not agent_dir.exists():
        print(f"Agent directory not found: {agent_dir}")
        sys.exit(1)

    server, config = create_agent_server(agent_dir)
    
    print(f"🤖 Starting {config['agent_name']}...")
    print(f"🌐 Server: http://{config['host']}:{config['port']}")
    print(f"📋 Agent Card: http://{config['host']}:{config['port']}/.well-known/agent.json")
    print(f"📁 Agent Dir: {agent_dir}")

    uvicorn.run(server.build(), host=config['host'], port=config['port'])


if __name__ == "__main__":
    main()
