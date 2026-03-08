#!/usr/bin/env python3
"""
Initialize a new team directory structure
"""
import os
import shutil
from pathlib import Path
import argparse


def create_team_directory(team_path: Path, force: bool = False):
    """Create a new team directory with template files"""
    
    if team_path.exists():
        if not force:
            print(f"❌ Directory {team_path} already exists")
            print("   Use --force to overwrite")
            return False
        shutil.rmtree(team_path)
    
    # Create team directory
    team_path.mkdir(parents=True)
    
    # Get template directory
    template_dir = Path(__file__).parent / "templates"
    
    # Copy config.yml
    config_src = template_dir / "config.yml"
    config_dst = team_path / "config.yml"
    shutil.copy2(config_src, config_dst)
    
    print(f"✅ Created team directory: {team_path}")
    print(f"📝 Created config file: {config_dst}")
    print()
    print("📋 Next steps:")
    print(f"   1. Edit {config_dst} to add your agents")
    print("   2. Create agent subdirectories:")
    print(f"      mkdir {team_path}/agent1")
    print(f"      mkdir {team_path}/agent2")
    print("   3. Add CLAUDE.md files to each agent directory")
    print("   4. Run your team:")
    print(f"      cc-team {team_path}")
    
    return True


def create_agent_directory(team_path: Path, agent_name: str, force: bool = False):
    """Create a new agent directory with template files"""
    
    agent_path = team_path / agent_name
    
    if agent_path.exists():
        if not force:
            print(f"❌ Agent directory {agent_path} already exists")
            return False
        shutil.rmtree(agent_path)
    
    # Create agent directory and .claude subdirectory
    agent_path.mkdir()
    (agent_path / ".claude").mkdir()
    
    # Copy CLAUDE.md template
    template_dir = Path(__file__).parent / "templates"
    claude_src = template_dir / "CLAUDE.md"
    claude_dst = agent_path / "CLAUDE.md"
    
    # Replace placeholder in template
    with open(claude_src, 'r') as f:
        content = f.read()
    content = content.replace("[AGENT_NAME]", agent_name.capitalize())
    
    with open(claude_dst, 'w') as f:
        f.write(content)
    
    print(f"✅ Created agent directory: {agent_path}")
    print(f"📝 Created personality file: {claude_dst}")
    print(f"📁 Created tool directory: {agent_path}/.claude")
    
    return True


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Initialize a new cc-team")
    parser.add_argument("command", choices=["init", "add-agent"], help="Command to run")
    parser.add_argument("path", help="Team directory path or agent name")
    parser.add_argument("--team", help="Team directory (for add-agent command)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing directories")
    
    args = parser.parse_args()
    
    if args.command == "init":
        team_path = Path(args.path)
        create_team_directory(team_path, args.force)
    
    elif args.command == "add-agent":
        if not args.team:
            print("❌ --team required for add-agent command")
            return
        
        team_path = Path(args.team)
        agent_name = args.path
        
        if not team_path.exists():
            print(f"❌ Team directory {team_path} does not exist")
            return
        
        create_agent_directory(team_path, agent_name, args.force)


if __name__ == "__main__":
    main()
