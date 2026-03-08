# CC-Team Samples

This directory contains example team configurations for the cc-team system.

## 📁 Directory Structure

```
samples/
├── README.md           # This file
├── team/               # Complete demo team
│   ├── config.yml      # Team configuration
│   ├── tom/            # Technical specialist
│   ├── jerry/          # Research analyst
│   └── alice/          # Project manager
└── my-new-team/        # Template team
    ├── config.yml      # Basic configuration
    └── developer/      # Template agent
```

## 🚀 Usage

### Run the Demo Team
```bash
cc-team samples/team
```

This starts a complete team with three specialized agents:
- **Tom**: Technical specialist for coding and architecture
- **Jerry**: Research analyst for information gathering
- **Alice**: Project manager for coordination

### Use as Template
```bash
# Copy the template
cp -r samples/my-new-team my-custom-team

# Customize the configuration
nano my-custom-team/config.yml

# Add more agents
cc-team my-custom-team --add-agent designer
cc-team my-custom-team --add-agent tester

# Run your custom team
cc-team my-custom-team
```

## 📋 What's Included

### Demo Team (`samples/team`)
- **Full configuration** with 3 agents
- **Detailed personalities** in CLAUDE.md files
- **Port management** (8001-8003)
- **Ready to run** out of the box

### Template Team (`samples/my-new-team`)
- **Basic config.yml** structure
- **Template CLAUDE.md** with placeholders
- **Single developer agent** 
- **Starting point** for custom teams

## 🎯 Learning Examples

### 1. Agent Personalities
Check the `CLAUDE.md` files in `samples/team/` to see how to define different agent personalities and roles.

### 2. Configuration Structure
Study `samples/team/config.yml` to understand:
- Agent definitions
- Port assignments
- Global settings

### 3. Team Organization
See how the demo team is structured with complementary roles:
- Technical (Tom)
- Research (Jerry) 
- Management (Alice)

## 🔧 Customization Tips

1. **Copy a sample** as starting point
2. **Edit config.yml** to match your needs
3. **Customize CLAUDE.md** for each agent's personality
4. **Add .claude/` directories for custom tools
5. **Test with** `cc-team your-team-directory`

## 📚 More Examples

For more advanced examples and use cases, see the main documentation.
