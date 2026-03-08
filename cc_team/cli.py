"""
Command Line Interface for cc-team
"""
import asyncio
import sys
import argparse
from pathlib import Path
from .team_manager import TeamManager
from .agent_spawner import AgentSpawner
from .ui.dashboard import TeamDashboard


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Claude Code Team System")
    parser.add_argument("team_directory", help="Path to team directory")
    parser.add_argument("--init", action="store_true", help="Initialize new team")
    parser.add_argument("--add-agent", help="Add new agent to team")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    # Handle init command
    if args.init:
        from .init import create_team_directory
        team_path = Path(args.team_directory)
        if create_team_directory(team_path, args.force):
            return
        else:
            sys.exit(1)
    
    # Handle add-agent command
    if args.add_agent:
        from .init import create_agent_directory
        team_path = Path(args.team_directory)
        if create_agent_directory(team_path, args.add_agent, args.force):
            return
        else:
            sys.exit(1)
    
    team_directory = Path(args.team_directory)
    
    try:
        # Initialize team manager
        team_manager = TeamManager(team_directory)
        
        # Parse team structure
        print(f"📁 Parsing team directory: {team_directory}")
        agents = team_manager.parse_team_structure()
        
        if not agents:
            print("❌ No agents found in team directory")
            sys.exit(1)
        
        # Validate team configuration
        issues = team_manager.validate_team()
        if issues:
            print("⚠️  Team configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
            
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        # Show team summary
        summary = team_manager.get_team_summary()
        print(f"✅ Found {summary['agents']} agents:")
        for member in summary['members']:
            status = "✅" if member['has_personality'] and member['has_claude_dir'] else "⚠️"
            print(f"   {status} {member['name']} -> {member['host']}:{member['port']}")
        
        # Initialize agent spawner
        spawner = AgentSpawner(team_manager)
        spawner.setup_signal_handlers()
        
        # Start all agents
        print("\n🚀 Starting team...")
        if not await spawner.start_all_agents():
            print("❌ Failed to start some agents")
            sys.exit(1)
        
        # Start the dashboard
        print("\n🖥️  Starting team dashboard...")
        dashboard = TeamDashboard(team_manager, spawner)
        
        try:
            # Run dashboard and monitor agents concurrently
            await asyncio.gather(
                dashboard.run_async(),
                spawner.monitor_agents()
            )
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            await spawner.stop_all_agents()
            print("👋 Goodbye!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cli_main():
    """Entry point for console script"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
