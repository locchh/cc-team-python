#!/usr/bin/env python3
"""
Simple script to run a cc-team
Usage: python3 run_team.py samples/team
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cc_team.team_manager import TeamManager
from cc_team.agent_spawner import AgentSpawner


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run_team.py <team_directory>")
        return
    
    team_dir = Path(sys.argv[1])
    
    # Load team
    print(f"📁 Loading team: {team_dir}")
    team_manager = TeamManager(team_dir)
    agents = team_manager.parse_team_structure()
    
    if not agents:
        print("❌ No agents found")
        return
    
    print(f"✅ Found {len(agents)} agents:")
    for name, config in agents.items():
        print(f"   {name}: {config.host}:{config.port}")
    
    # Start agents
    spawner = AgentSpawner(team_manager)
    print("\n🚀 Starting agents...")
    
    if await spawner.start_all_agents():
        print("\n🎉 Team running! Press Ctrl+C to stop")
        print("🔗 Agents available:")
        for name, config in agents.items():
            print(f"   {name}: http://{config.host}:{config.port}")
        
        try:
            await asyncio.sleep(float('inf'))
        except KeyboardInterrupt:
            pass
        
        print("\n🛑 Stopping agents...")
        await spawner.stop_all_agents()
        print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
