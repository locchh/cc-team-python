#!/usr/bin/env python3
"""
Team UI - Textual monitoring dashboard for team agents
Usage: python3 misc/team_ui.py samples/team [--debug]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cc_team.tui import run_team_tui


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 team_ui.py <team_directory>")
        print("Example: python3 team_ui.py samples/team")
        return

    team_dir = Path(sys.argv[1])
    if not team_dir.exists():
        print(f"❌ Team directory not found: {team_dir}")
        return

    run_team_tui(team_dir)


if __name__ == "__main__":
    main()
