# cc-team

```bash        
    █████████     █████████     █████████ 
    ██ ███ ██     ██ ███ ██     ██ ███ ██ 
...███████████---███████████---███████████...
    █████████     █████████     █████████ 
      █   █         █   █         █   █   
```

Spawn a team of Claude Code instances, each running as an A2A agent. They communicate with each other via the A2A protocol and can be monitored through a real-time TUI dashboard.

## Usage

```bash
# Run directly from GitHub (no install needed)
uvx --from git+https://github.com/locchh/snx cc-team run /path/to/your/team

# Or install locally
uv pip install -e .
cc-team run samples/team
cc-team validate samples/team
cc-team help
```

## Team structure

```
my-team/
├── config.yml
├── tom/
│   ├── CLAUDE.md       # Agent persona / system prompt
│   └── .claude/
├── jerry/
│   ├── CLAUDE.md
│   └── .claude/
└── alice/
    ├── CLAUDE.md
    └── .claude/
```

`config.yml`:
```yaml
team:
  name: "My Team"
agents:
  tom:
    host: localhost
    port: 8001
    model: claude-opus-4-6        # per-agent model override
  jerry:
    host: localhost
    port: 8002
settings:
  model: claude-sonnet-4-6        # default model for all agents
  auto_increment_ports: true
```

Available models: `claude-haiku-4-5-20251001` · `claude-sonnet-4-6` · `claude-opus-4-6`

## Related

- [A2A Documentation](https://a2a-protocol.org/latest/)
- [A2A Repository](https://github.com/a2aproject/A2A)
- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Textual](https://github.com/Textualize/textual)
