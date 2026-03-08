"""
Team Dashboard - Textual UI for managing agent teams
"""
import asyncio
import httpx
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label, Input, TextArea
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from ..team_manager import TeamManager
from ..agent_spawner import AgentSpawner


class MessageScreen(ModalScreen):
    """Screen for sending messages to agents"""
    
    def __init__(self, agent_name: str, agent_host: str, agent_port: int):
        super().__init__()
        self.agent_name = agent_name
        self.agent_url = f"http://{agent_host}:{agent_port}"
    
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Message {self.agent_name}", id="title"),
            TextArea(placeholder="Type your message here...", id="message"),
            Horizontal(
                Button("Send", id="send"),
                Button("Cancel", id="cancel")
            ),
            id="dialog"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send":
            message = self.query_one("#message", TextArea).text
            self.dismiss(message)
        else:
            self.dismiss(None)


class TeamDashboard(App):
    """Main dashboard for managing agent teams"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #title {
        text-align: center;
        padding: 1;
    }
    
    #agents-panel {
        width: 30%;
        height: 100%;
        border: solid $primary;
    }
    
    #status-panel {
        width: 40%;
        height: 100%;
        border: solid $accent;
        padding: 1;
    }
    
    #chat-panel {
        width: 30%;
        height: 100%;
        border: solid $success;
        padding: 1;
    }
    
    .button {
        margin: 1;
    }
    
    #dialog {
        width: 60;
        height: 20;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }
    
    #title {
        text-align: center;
        text-style: bold;
    }
    
    .agent-status {
        padding: 1;
        margin: 1;
        border: solid $panel;
    }
    
    .status-running {
        border-color: $success;
    }
    
    .status-stopped {
        border-color: $error;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("m", "send_message", "Send Message"),
        Binding("s", "start_agent", "Start Agent"),
        Binding("x", "stop_agent", "Stop Agent"),
    ]
    
    selected_agent: reactive[str] = reactive("")
    
    def __init__(self, team_manager: TeamManager, spawner: AgentSpawner):
        super().__init__()
        self.team_manager = team_manager
        self.spawner = spawner
    
    async def on_mount(self) -> None:
        """Initialize the dashboard"""
        self.title = "Claude Code Team Dashboard"
        self.set_interval(2.0, self.refresh_status)  # Auto-refresh every 2 seconds
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Label("Team Members", id="title"),
                ListView(id="agents_list"),
                Vertical(
                    Button("Start Agent", id="start_btn"),
                    Button("Stop Agent", id="stop_btn"),
                    Button("Send Message", id="message_btn"),
                    id="agent_actions"
                ),
                id="agents-panel"
            ),
            Vertical(
                Label("Team Status", id="title"),
                Static("Select an agent to view status", id="agent_status"),
                Static("Team Overview:", id="team_overview"),
                id="status-panel"
            ),
            Vertical(
                Label("Chat Log", id="title"),
                Static("Messages will appear here...", id="chat_log"),
                Input(placeholder="Type message here...", id="chat_input"),
                Button("Send", id="send_chat"),
                id="chat-panel"
            )
        )
        yield Footer()
    
    async def refresh_agents_list(self):
        """Refresh the agents list"""
        agents = self.team_manager.get_agent_configs()
        agents_list = self.query_one("#agents_list", ListView)
        agents_list.clear()
        
        for agent_name, config in agents.items():
            status = self.spawner.get_agent_status().get(agent_name, {})
            is_running = status.get("running", False)
            
            status_icon = "🟢" if is_running else "🔴"
            item = ListItem(Label(f"{status_icon} {agent_name} ({config.host}:{config.port})"))
            item.agent_name = agent_name
            agents_list.append(item)
    
    async def refresh_status(self):
        """Refresh status display"""
        if self.selected_agent:
            await self.show_agent_status(self.selected_agent)
        
        # Update team overview
        agent_status = self.spawner.get_agent_status()
        running_count = sum(1 for status in agent_status.values() if status.get("running", False))
        total_count = len(agent_status)
        
        overview = f"Team Status: {running_count}/{total_count} agents running"
        self.query_one("#team_overview", Static).update(overview)
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle agent selection"""
        agent_name = event.item.agent_name
        self.selected_agent = agent_name
        await self.show_agent_status(agent_name)
    
    async def show_agent_status(self, agent_name: str):
        """Show status for selected agent"""
        config = self.team_manager.get_agent_config(agent_name)
        status = self.spawner.get_agent_status().get(agent_name, {})
        
        if not config:
            self.query_one("#agent_status", Static).update("Agent not found")
            return
        
        is_running = status.get("running", False)
        pid = status.get("pid", "N/A")
        
        status_text = f"""
Agent: {agent_name}
Host: {config.host}
Port: {config.port}
Status: {'🟢 Running' if is_running else '🔴 Stopped'}
PID: {pid}
Personality: {'✅' if config.personality else '❌ Missing'}
Claude Dir: {'✅' if (config.directory / '.claude').exists() else '❌ Missing'}
        """.strip()
        
        self.query_one("#agent_status", Static).update(status_text)
    
    async def action_send_message(self) -> None:
        """Send message to selected agent"""
        if not self.selected_agent:
            self.query_one("#chat_log", Static).update("❌ Please select an agent first")
            return
        
        config = self.team_manager.get_agent_config(self.selected_agent)
        if not config:
            return
        
        message = await self.push_screen(MessageScreen(self.selected_agent, config.host, config.port))
        if message:
            await self.send_message_to_agent(config.host, config.port, message)
    
    async def send_message_to_agent(self, host: str, port: int, message: str):
        """Send message to agent via A2A protocol"""
        try:
            async with httpx.AsyncClient() as client:
                message_data = {
                    "jsonrpc": "2.0",
                    "id": "dashboard",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "messageId": "dashboard-msg",
                            "role": "user",
                            "parts": [{"text": message}]
                        }
                    }
                }
                
                response = await client.post(
                    f"http://{host}:{port}/",
                    json=message_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        result_data = result["result"]
                        if result_data.get("kind") == "message":
                            for part in result_data.get("parts", []):
                                if "text" in part:
                                    response_text = part["text"]
                                    chat_log = self.query_one("#chat_log", Static)
                                    current_log = chat_log.renderable or ""
                                    new_log = f"You: {message}\nAgent: {response_text}\n\n{current_log}"
                                    chat_log.update(new_log[-500:])  # Keep last 500 chars
                else:
                    self.query_one("#chat_log", Static).update(f"❌ Error: {response.status_code}")
        
        except Exception as e:
            self.query_one("#chat_log", Static).update(f"❌ Connection error: {e}")
    
    async def action_start_agent(self) -> None:
        """Start selected agent"""
        if not self.selected_agent:
            return
        
        success = await self.spawner.start_agent(self.selected_agent)
        if success:
            await self.refresh_agents_list()
            await self.refresh_status()
    
    async def action_stop_agent(self) -> None:
        """Stop selected agent"""
        if not self.selected_agent:
            return
        
        success = await self.spawner.stop_agent(self.selected_agent)
        if success:
            await self.refresh_agents_list()
            await self.refresh_status()
    
    async def action_refresh(self) -> None:
        """Refresh dashboard"""
        await self.refresh_agents_list()
        await self.refresh_status()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "message_btn":
            await self.action_send_message()
        elif event.button.id == "start_btn":
            await self.action_start_agent()
        elif event.button.id == "stop_btn":
            await self.action_stop_agent()
        elif event.button.id == "send_chat":
            chat_input = self.query_one("#chat_input", Input)
            if chat_input.value and self.selected_agent:
                config = self.team_manager.get_agent_config(self.selected_agent)
                if config:
                    await self.send_message_to_agent(config.host, config.port, chat_input.value)
                    chat_input.value = ""
