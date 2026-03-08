# Claude Code + A2A

## Structure

Structure of repo:

```
snx/
├── 📦 cc_team/              # Main package
├── 📋 pyproject.toml        # Modern packaging
├── 📚 USAGE.md              # Complete usage guide
├── 🧪 test_*.py            # Test scripts
├── 🤖 dynamic_agent.py     # Core agent system
├── 📁 samples/              # Example teams!
│   ├── team/                # Demo team (Tom, Jerry, Alice)
│   └── my-new-team/         # Template team
└── 📄 README.md             # Project overview
```

Structure of team:

```
team/
├── tom
│   ├── .claude/
│   └── CLAUDE.md
├── jerry
│   ├── .claude/
│   └── CLAUDE.md
├── bob
│   ├── .claude/
│   └── CLAUDE.md
├── alice
│   ├── .claude/
│   └── CLAUDE.md
...
```

Usage: When running `cc-team <path/to/your/team>`, It will spawm a team of Claude Code instances, each instance is a member of the team. They can communicate with each other using A2A protocol. and you can interact with them through TUI (Textual)

## Related to

[A2A Documentation](https://a2a-protocol.org/latest/)

[A2A Repository](https://github.com/a2aproject/A2A)

[Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)

[A2A MCP Server - LocCH](https://github.com/locchh/A2A-MCP-Server)

[A2A MCP Server - GongRzhe](https://github.com/GongRzhe/A2A-MCP-Server)

[Textual](https://github.com/Textualize/textual)