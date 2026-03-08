"""
Team TUI - Message monitor dashboard using Textual
Each agent gets a full-height vertical pane side by side.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from textual.app import ComposeResult, App
from textual.containers import Horizontal, Vertical
from textual.widgets import RichLog, Header, Footer, Static
from textual.binding import Binding
from rich.text import Text

from .team_manager import TeamManager
from .agent_spawner import AgentSpawner
from .message_capture import (
    get_global_message_capture,
    MessageType,
    CapturedMessage,
)


class AgentPanel(Vertical):
    """Full-height vertical pane for a single agent."""

    DEFAULT_CSS = """
    AgentPanel {
        width: 1fr;
        height: 1fr;
        border-left: solid $panel;
    }

    AgentPanel:first-child {
        border-left: none;
    }

    AgentPanel.running {
        border-left: solid $success;
    }

    AgentPanel.stopped {
        border-left: solid $error;
    }

    AgentPanel.focused {
        border-left: solid $accent;
    }

    AgentPanel > #panel-header {
        height: 7;
        background: $boost;
        padding: 0 1;
        content-align: center middle;
    }

    AgentPanel > RichLog {
        height: 1fr;
        background: $surface;
        scrollbar-gutter: stable;
    }
    """

    def __init__(self, agent_name: str, host: str, port: int, spawner: AgentSpawner):
        super().__init__()
        self.agent_name = agent_name
        self.host = host
        self.port = port
        self.spawner = spawner
        self._log_widget: Optional[RichLog] = None
        self._agent_running = False
        self._newest_ts: float = 0.0  # track newest message timestamp (bug 2)

    def compose(self) -> ComposeResult:
        yield Static(self._make_header(), id="panel-header")
        log = RichLog(markup=True, highlight=False, wrap=True)
        self._log_widget = log
        yield log

    # Pixel-art Claude face (orange, ~5 lines)
    _CLAUDE_ART = (
        "[#d4682a]           [/]",
        "[#d4682a] █████████ [/]",
        "[#d4682a] ██ ███ ██ [/]",
        "[#d4682a]███████████[/]",
        "[#d4682a] █████████ [/]",
        "[#d4682a]   █   █   [/]",
    )

    def _make_header(self) -> str:
        dot = "[bold green]●[/bold green]" if self._agent_running else "[dim]○[/dim]"
        port_info = f"[dim]:{self.port}[/dim]"
        art = "\n".join(self._CLAUDE_ART)
        return f"{art}\n {dot} [bold]{self.agent_name}[/bold]{port_info}"

    def update_header(self) -> None:
        self.query_one("#panel-header", Static).update(self._make_header())

    async def update_messages(self) -> None:
        if not self._log_widget:
            return

        capture = get_global_message_capture()
        # newest-first from get_messages; reversed() below makes oldest-first for display
        messages = await capture.get_messages(agent_name=self.agent_name, limit=50)

        if not messages or messages[0].timestamp == self._newest_ts:
            return

        self._newest_ts = messages[0].timestamp
        self._log_widget.clear()

        for msg in reversed(messages):  # oldest-first for chronological display
            self._render_message(msg)

    def _render_message(self, msg: CapturedMessage) -> None:
        if not self._log_widget:
            return

        # Skip bare HTTP status lines — the real response is captured separately
        if msg.content.startswith("[Response:"):
            return

        ts = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S")

        if msg.direction == "incoming":
            if msg.message_type == MessageType.AGENT_TO_AGENT:
                arrow = "[bold green]▶[/bold green]"
                body = self._extract_text(msg.content)
            elif msg.message_type == MessageType.SYSTEM_EVENT:
                return  # skip health/system noise
            else:
                arrow = "[cyan]▶[/cyan]"
                body = f"[dim]{msg.message_type.value}[/dim]"
        else:
            # Actual agent response text
            arrow = "[bold blue]◀[/bold blue]"
            body = msg.content

        self._log_widget.write(
            Text.from_markup(f"[dim]{ts}[/dim] {arrow} {body}")
        )

    def _extract_text(self, content: str) -> str:
        if not content or not content.strip():
            return "[dim]<empty>[/dim]"
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # params.message.parts[0].text
                parts = data.get("params", {}).get("message", {}).get("parts", [])
                if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                    t = parts[0]["text"]
                    return t[:120] if len(t) > 120 else t
                if "method" in data:
                    return f"[dim]rpc:{data['method']}[/dim]"
            return f"[dim]{json.dumps(data)[:100]}[/dim]"
        except (json.JSONDecodeError, TypeError):
            return content[:120] if len(content) > 120 else content

    def update_status(self, is_running: bool) -> None:
        self._agent_running = is_running
        self.update_header()
        # Only toggle running/stopped — never touch focused (bug 1)
        self.remove_class("running", "stopped")
        self.add_class("running" if is_running else "stopped")


class TeamTUI(App):
    """Team monitoring dashboard — agents as vertical panes."""

    TITLE = "TeamTUI"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+a", "start_all", "Start All"),
        Binding("ctrl+x", "stop_all", "Stop All"),
        Binding("s", "start_focused", "Start"),
        Binding("x", "stop_focused", "Stop"),
        Binding("c", "clear_focused", "Clear"),
        Binding("tab", "focus_next", "Next Panel"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #panels {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, team_dir: Path):
        super().__init__()
        self.team_dir = Path(team_dir)
        self.team_manager: Optional[TeamManager] = None
        self.spawner: Optional[AgentSpawner] = None
        self.agent_panels: Dict[str, AgentPanel] = {}
        self.focused_agent: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(id="panels")
        yield Footer()

    async def on_mount(self) -> None:
        self.title = f"TeamTUI — {self.team_dir.name}"

        self.team_manager = TeamManager(self.team_dir)
        self.team_manager.parse_team_structure()
        self.spawner = AgentSpawner(self.team_manager)

        container = self.query_one("#panels", Horizontal)
        agent_names = sorted(self.team_manager.get_agent_configs().keys())

        for name in agent_names:
            cfg = self.team_manager.get_agent_config(name)
            panel = AgentPanel(name, cfg.host, cfg.port, self.spawner)
            self.agent_panels[name] = panel
            await container.mount(panel)

        if agent_names:
            self.focused_agent = agent_names[0]
            self.agent_panels[agent_names[0]].add_class("focused")

        self.set_interval(2.0, self._poll_messages)
        self.set_interval(5.0, self._poll_agent_status)

        # Auto-start all agents
        await self.spawner.start_all_agents()

    async def _poll_messages(self) -> None:
        for panel in self.agent_panels.values():
            await panel.update_messages()

    async def _poll_agent_status(self) -> None:
        if not self.spawner:
            return
        status = self.spawner.get_agent_status()
        for name, panel in self.agent_panels.items():
            panel.update_status(status.get(name, {}).get("running", False))

    async def action_start_all(self) -> None:
        if self.spawner:
            await self.spawner.start_all_agents()

    async def action_stop_all(self) -> None:
        if self.spawner:
            await self.spawner.stop_all_agents()

    async def action_start_focused(self) -> None:
        if self.spawner and self.focused_agent:
            await self.spawner.start_agent(self.focused_agent)

    async def action_stop_focused(self) -> None:
        if self.spawner and self.focused_agent:
            await self.spawner.stop_agent(self.focused_agent)

    def action_clear_focused(self) -> None:
        if self.focused_agent and self.focused_agent in self.agent_panels:
            panel = self.agent_panels[self.focused_agent]
            if panel._log_widget:
                panel._log_widget.clear()
                panel.last_message_count = 0

    def action_focus_next(self) -> None:
        names = sorted(self.agent_panels.keys())
        if not names:
            return
        # Remove focused style from current (bug 3: guard against None / stale key)
        if self.focused_agent and self.focused_agent in self.agent_panels:
            self.agent_panels[self.focused_agent].remove_class("focused")
        idx = names.index(self.focused_agent) if self.focused_agent in names else 0
        self.focused_agent = names[(idx + 1) % len(names)]
        self.agent_panels[self.focused_agent].add_class("focused")

    async def action_quit(self) -> None:
        if self.spawner:
            await self.spawner.stop_all_agents()
        self.exit()


def run_team_tui(team_dir: Path) -> None:
    app = TeamTUI(team_dir)
    app.run()
