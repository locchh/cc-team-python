"""
Agent Spawner - Manages lifecycle of team agents
"""
import sys
import asyncio
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .team_manager import AgentConfig, TeamManager


class AgentProcess:
    """Represents a running agent process"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        
    async def start(self) -> bool:
        """Start the agent process"""
        try:
            # Use the dynamic_agent.py script
            cmd = [
                sys.executable, 
                str(Path(__file__).parent.parent / "dynamic_agent.py"),
                str(self.config.directory)
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.is_running = True
            print(f"🚀 Started agent {self.config.name} on {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start agent {self.config.name}: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the agent process"""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                await asyncio.sleep(1)  # Give it time to shutdown
                
                if self.process.poll() is None:
                    self.process.kill()  # Force kill if still running
                
                self.is_running = False
                print(f"🛑 Stopped agent {self.config.name}")
                return True
                
            except Exception as e:
                print(f"❌ Failed to stop agent {self.config.name}: {e}")
                return False
        
        return False
    
    def is_alive(self) -> bool:
        """Check if agent process is still running"""
        return self.process and self.process.poll() is None and self.is_running


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
        
        success_count = 0
        for agent_name, agent_process in self.agent_processes.items():
            if await agent_process.stop():
                success_count += 1
        
        self.agent_processes.clear()
        self.is_running = False
        
        if success_count == len(self.agent_processes):
            print(f"✅ All {success_count} agents stopped successfully")
            return True
        else:
            print(f"⚠️  Stopped {success_count}/{len(self.agent_processes)} agents")
            return False
    
    async def start_agent(self, agent_name: str) -> bool:
        """Start a specific agent"""
        if agent_name in self.agent_processes and self.agent_processes[agent_name].is_running:
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
                "pid": agent_process.process.pid if agent_process.process else None
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
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down agents...")
            asyncio.create_task(self.stop_all_agents())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
