#!/usr/bin/env python3
"""
Standalone cc-team CLI that can be run from anywhere
"""
import sys
import os

# Add the current directory to Python path to import cc_team
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from cc_team.cli import cli_main

if __name__ == "__main__":
    cli_main()
