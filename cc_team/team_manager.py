"""
Team Manager - Parses team directory structure and manages team configuration
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for a single agent"""

    name: str
    directory: Path
    config: Dict
    agent_definition: str
    host: str
    port: int


class TeamManager:
    """Manages team configuration and agent discovery"""

    def __init__(self, team_directory: Path):
        self.team_directory = Path(team_directory)
        self.agents: Dict[str, AgentConfig] = {}
        self.team_config = {}

    def parse_team_structure(self) -> Dict[str, AgentConfig]:
        """Parse team directory structure and load agent configurations"""
        if not self.team_directory.exists():
            raise ValueError(f"Team directory not found: {self.team_directory}")

        # Load central config.yml
        self._load_team_config()

        self.agents = {}

        # Find all agent subdirectories
        for agent_dir in self.team_directory.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith("."):
                agent_config = self._parse_agent_config(agent_dir)
                if agent_config:
                    self.agents[agent_config.name] = agent_config

        return self.agents

    def _load_team_config(self):
        """Load central team configuration"""
        config_file = self.team_directory / "config.yml"
        if config_file.exists():
            with open(config_file, "r") as f:
                self.team_config = yaml.safe_load(f) or {}
        else:
            self.team_config = {"agents": {}, "settings": {}}

    def _parse_agent_config(self, agent_dir: Path) -> Optional[AgentConfig]:
        """Parse configuration for a single agent"""
        try:
            agent_name = agent_dir.name

            # Get agent config from central config.yml
            agent_config_data = self.team_config.get("agents", {}).get(agent_name, {})

            # Load agent definition from CLAUDE.md
            agent_definition_file = agent_dir / "CLAUDE.md"
            agent_definition = ""
            if agent_definition_file.exists():
                with open(agent_definition_file, "r") as f:
                    agent_definition = f.read().strip()

            # Use central config or defaults
            settings = self.team_config.get("settings", {})
            host = agent_config_data.get(
                "host", settings.get("default_host", "localhost")
            )

            # Port assignment
            if "port" in agent_config_data:
                port = agent_config_data["port"]
            elif settings.get("auto_increment_ports", True):
                port = settings.get("base_port", 8001) + len(self.agents)
            else:
                port = 8001 + len(self.agents)

            description = agent_config_data.get(
                "description", f"A2A agent: {agent_name}"
            )

            return AgentConfig(
                name=agent_name,
                directory=agent_dir,
                config={
                    "agent_name": agent_name,
                    "host": host,
                    "port": port,
                    "description": description,
                    **agent_config_data,
                },
                agent_definition=agent_definition,
                host=host,
                port=port,
            )

        except Exception as e:
            print(f"Error parsing agent config for {agent_dir.name}: {e}")
            return None

    def get_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations"""
        return self.agents

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_name)

    def validate_team(self) -> List[str]:
        """Validate team configuration and return list of issues"""
        issues = []

        if not self.agents:
            issues.append("No agents found in team directory")
            return issues

        # Check for port conflicts
        used_ports = set()
        for agent_name, agent_config in self.agents.items():
            if agent_config.port in used_ports:
                issues.append(
                    f"Port conflict: {agent_name} uses port {agent_config.port}"
                )
            used_ports.add(agent_config.port)

        # Check for missing agent definition files
        for agent_name, agent_config in self.agents.items():
            if not agent_config.agent_definition:
                issues.append(f"Missing CLAUDE.md for agent: {agent_name}")

        # Check for missing .claude directories
        for agent_name, agent_config in self.agents.items():
            claude_dir = agent_config.directory / ".claude"
            if not claude_dir.exists():
                issues.append(f"Missing .claude directory for agent: {agent_name}")

        return issues

    def get_team_summary(self) -> Dict:
        """Get summary of team configuration"""
        if not self.agents:
            return {"agents": 0, "members": []}

        members = []
        for agent_name, agent_config in self.agents.items():
            members.append(
                {
                    "name": agent_name,
                    "host": agent_config.host,
                    "port": agent_config.port,
                    "has_agent_definition": bool(agent_config.agent_definition),
                    "has_claude_dir": (agent_config.directory / ".claude").exists(),
                }
            )

        return {
            "agents": len(self.agents),
            "team_directory": str(self.team_directory),
            "members": members,
        }
