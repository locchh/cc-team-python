"""
Agent Spawner - Manages lifecycle of team agents
"""

import asyncio
import subprocess
import uvicorn
from typing import Dict, Optional
from .team_manager import AgentConfig, TeamManager

# A2A imports for inline agent logic
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from dotenv import load_dotenv
from .message_capture import get_global_message_capture, MessageCaptureMiddleware, MessageType

# Claude SDK imports
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import tool, create_sdk_mcp_server


class InlineAgentExecutor(AgentExecutor):
    """Inline A2A agent using Claude SDK with configurable agent definition"""

    _ = load_dotenv(override=True)

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.agent_definition = config.agent_definition
        self.claude_client = None
        self.setup_complete = False

    async def setup_claude(self):
        """Setup Claude SDK with custom tools"""
        if self.setup_complete:
            return

        @tool("get_agent_info", "Get information about this agent", {})
        async def get_agent_info(args):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"I am {self.config.name}, an AI agent. {self.config.config.get('description', '')}",
                    }
                ]
            }

        @tool("get_team_members", "Get information about team members", {})
        async def get_team_members(args):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "I can communicate with other team members via A2A protocol. We work together to solve complex problems.",
                    }
                ]
            }

        server = create_sdk_mcp_server(
            name=f"{self.config.name}-tools",
            version="1.0.0",
            tools=[get_agent_info, get_team_members],
        )

        system_prompt = f"{self.agent_definition}\n\nYou are part of a team of AI agents. You can communicate with other team members using the A2A protocol. Be helpful, collaborative, and work together with your team."

        options = ClaudeAgentOptions(
            mcp_servers={"tools": server},
            allowed_tools=[
                "mcp__tools__get_agent_info",
                "mcp__tools__get_team_members",
            ],
            system_prompt=system_prompt,
        )

        self.claude_client = ClaudeSDKClient(options=options)
        self.setup_complete = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute agent task using Claude SDK"""
        if not self.setup_complete:
            await self.setup_claude()

        prompt = context.get_user_input()

        response_text = ""
        try:
            async with self.claude_client:
                await self.claude_client.query(prompt)

                async for msg in self.claude_client.receive_response():
                    if hasattr(msg, "content"):
                        for block in msg.content:
                            if hasattr(block, "text"):
                                response_text += block.text
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ Claude SDK error for agent {self.config.name}: {e}")
            response_text = f"Error processing request: {e}"

        # Bug 5: fall back so clients never get a silent blank response
        if not response_text:
            response_text = "[No response]"

        # Capture actual response text (bug 4: use module-level import)
        await get_global_message_capture().capture(
            agent_name=self.config.name,
            direction="outgoing",
            message_type=MessageType.AGENT_RESPONSE,
            content=response_text,
        )

        await event_queue.enqueue_event(new_agent_text_message(response_text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation"""
        pass


def create_agent_server(config: AgentConfig):
    """Create A2A server for a specific agent with message capture"""
    agent_executor = InlineAgentExecutor(config)

    skill = AgentSkill(
        id="team_collaboration",
        name="Team Collaboration",
        description="AI agent that works with other team members",
        tags=["team", "collaboration", "a2a"],
        examples=[
            "What can you help me with?",
            "Can you work with your team on this?",
            "Tell me about your capabilities",
        ],
    )

    agent_card = AgentCard(
        name=config.name,
        description=config.config.get("description", f"A2A agent: {config.name}"),
        url=f"http://{config.host}:{config.port}/",
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

    # Build the app with middleware
    message_capture = get_global_message_capture()

    # Get the original app from A2A server and add middleware
    app = server.build()

    # Add middleware to the existing app
    app.add_middleware(
        MessageCaptureMiddleware,
        agent_name=config.name,
        message_capture=message_capture,
    )

    return app


class AgentProcess:
    """Represents a running agent process"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self) -> bool:
        """Start the agent process using inline logic"""
        try:
            # Create agent server with message capture
            app = create_agent_server(self.config)

            # Start server in background task
            self.task = asyncio.create_task(self._run_server(app))

            # Yield to event loop so uvicorn starts binding before we report running (bug 6)
            await asyncio.sleep(0.1)
            if self.task.done():
                return False  # failed immediately (e.g. port in use)
            self.is_running = True
            print(
                f"🚀 Started agent {self.config.name} on {self.config.host}:{self.config.port}"
            )
            return True

        except Exception as e:
            print(f"❌ Failed to start agent {self.config.name}: {e}")
            return False

    async def _run_server(self, app):
        """Run the A2A server"""
        try:
            config = uvicorn.Config(
                app=app,
                host=self.config.host,
                port=self.config.port,
                log_level="error",  # Reduce log noise
            )
            # Create and run HTTP server
            server_instance = uvicorn.Server(config)
            await server_instance.serve()
        except Exception as e:
            print(f"❌ Agent {self.config.name} server error: {e}")
            self.is_running = False

    async def stop(self) -> bool:
        """Stop the agent process"""
        if self.task and self.is_running:
            try:
                self.task.cancel()
                try:
                    await self.task
                except (asyncio.CancelledError, Exception):
                    pass
                finally:
                    self.task = None

                self.is_running = False
                print(f"🛑 Stopped agent {self.config.name}")
                return True

            except Exception as e:
                print(f"❌ Failed to stop agent {self.config.name}: {e}")
                return False

        return False

    def is_alive(self) -> bool:
        """Check if agent process is still running"""
        return self.task and not self.task.done() and self.is_running


class AgentSpawner:
    """Manages spawning and lifecycle of all team agents"""

    def __init__(self, team_manager: TeamManager):
        self.team_manager = team_manager
        self.agent_processes: Dict[str, AgentProcess] = {}
        self.is_running = False

    async def start_all_agents(self) -> bool:
        """Start all agents in the team"""
        agent_configs = self.team_manager.get_agent_configs()

        if not agent_configs:
            print("❌ No agents found to start")
            return False

        print(f"🚀 Starting {len(agent_configs)} agents...")

        success_count = 0
        for agent_name, config in agent_configs.items():
            agent_process = AgentProcess(config)
            if await agent_process.start():
                self.agent_processes[agent_name] = agent_process
                success_count += 1
            else:
                print(f"❌ Failed to start agent: {agent_name}")

        if success_count == len(agent_configs):
            print(f"✅ All {success_count} agents started successfully")
            self.is_running = True
            return True
        else:
            print(f"⚠️  Started {success_count}/{len(agent_configs)} agents")
            self.is_running = success_count > 0
            return success_count > 0

    async def stop_all_agents(self) -> bool:
        """Stop all running agents"""
        if not self.agent_processes:
            print("ℹ️  No agents running")
            return True

        print(f"🛑 Stopping {len(self.agent_processes)} agents...")

        # Copy items to avoid dictionary changed size during iteration
        agent_items = list(self.agent_processes.items())
        success_count = 0

        for agent_name, agent_process in agent_items:
            if await agent_process.stop():
                success_count += 1

        self.agent_processes.clear()
        self.is_running = False

        total_agents = len(agent_items)
        if success_count == total_agents:
            print(f"✅ All {success_count} agents stopped successfully")
            return True
        else:
            print(f"⚠️  Stopped {success_count}/{total_agents} agents")
            return success_count > 0

    async def start_agent(self, agent_name: str) -> bool:
        """Start a specific agent"""
        if (
            agent_name in self.agent_processes
            and self.agent_processes[agent_name].is_running
        ):
            print(f"⚠️  Agent {agent_name} is already running")
            return False

        config = self.team_manager.get_agent_config(agent_name)
        if not config:
            print(f"❌ Agent {agent_name} not found")
            return False

        agent_process = AgentProcess(config)
        if await agent_process.start():
            self.agent_processes[agent_name] = agent_process
            return True

        return False

    async def stop_agent(self, agent_name: str) -> bool:
        """Stop a specific agent"""
        if agent_name not in self.agent_processes:
            print(f"❌ Agent {agent_name} not found")
            return False

        agent_process = self.agent_processes[agent_name]
        success = await agent_process.stop()

        if success:
            del self.agent_processes[agent_name]

        return success

    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all agents"""
        status = {}
        for agent_name, agent_process in self.agent_processes.items():
            status[agent_name] = {
                "name": agent_name,
                "host": agent_process.config.host,
                "port": agent_process.config.port,
                "running": agent_process.is_alive(),
                "task_id": id(agent_process.task) if agent_process.task else None,
            }

        return status

    async def monitor_agents(self):
        """Monitor agent processes and restart if needed"""
        # Disabled monitoring to prevent crash loops
        # Agents will be restarted manually if needed
        while self.is_running:
            await asyncio.sleep(30)  # Just sleep to keep the task alive

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        # Disabled signal handlers to prevent hanging
        pass
