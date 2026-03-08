"""
cc-team CLI entry point
"""

import sys
import argparse
from pathlib import Path


def cmd_help(args):
    print(
        """cc-team — Claude Code Team System

Commands:
  run <team_dir>       Start the team TUI dashboard
  validate <team_dir>  Validate a team directory structure

Examples:
  cc-team run samples/team
  cc-team validate samples/team
"""
    )


def cmd_validate(args):
    from .team_manager import TeamManager

    team_dir = Path(args.team_dir)
    if not team_dir.exists():
        print(f"❌ Directory not found: {team_dir}")
        sys.exit(1)

    manager = TeamManager(team_dir)
    try:
        manager.parse_team_structure()
    except Exception as e:
        print(f"❌ Failed to parse team: {e}")
        sys.exit(1)

    issues = manager.validate_team()
    summary = manager.get_team_summary()

    print(f"Team: {team_dir}")
    print(f"Agents found: {summary['agents']}")
    for member in summary["members"]:
        model = member.get("model") or "default"
        status = "✅" if member["has_agent_definition"] and member["has_claude_dir"] else "⚠️ "
        print(f"  {status} {member['name']}  {member['host']}:{member['port']}  [{model}]")

    if issues:
        print("\nIssues:")
        for issue in issues:
            print(f"  ❌ {issue}")
        sys.exit(1)
    else:
        print("\n✅ Team is valid")


def cmd_run(args):
    from pathlib import Path as P
    from .tui import run_team_tui

    team_dir = P(args.team_dir)
    if not team_dir.exists():
        print(f"❌ Directory not found: {team_dir}")
        sys.exit(1)

    run_team_tui(team_dir)


def main():
    parser = argparse.ArgumentParser(
        prog="cc-team",
        description="Claude Code Team System",
        add_help=True,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("help", help="Show this help message")

    p_validate = sub.add_parser("validate", help="Validate a team directory")
    p_validate.add_argument("team_dir", help="Path to team directory")

    p_run = sub.add_parser("run", help="Start the team TUI dashboard")
    p_run.add_argument("team_dir", help="Path to team directory")

    args = parser.parse_args()

    if args.command == "help" or args.command is None:
        cmd_help(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "run":
        cmd_run(args)
