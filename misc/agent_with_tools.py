"""
Agent with Custom Tools
Shows how to add tools to Claude SDK agents
"""
import asyncio
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("get_time", "Get current time", {})
async def get_time(args):
    """Simple tool to get current time"""
    import datetime
    now = datetime.datetime.now()
    return {
        "content": [{
            "type": "text",
            "text": f"Current time: {now.strftime('%H:%M:%S')}"
        }]
    }


@tool("calculate", "Simple calculator", {"expression": str})
async def calculate(args):
    """Simple calculator tool"""
    try:
        expression = args.get("expression", "")
        # Safe eval for simple math
        result = eval(expression)  # Only for demo - be careful with eval!
        return {
            "content": [{
                "type": "text", 
                "text": f"{expression} = {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {e}"
            }]
        }


async def main():
    print("🔧 Agent with Custom Tools Demo")
    print("=" * 40)
    
    # Create MCP server with tools
    server = create_sdk_mcp_server(
        name="demo-tools",
        version="1.0.0",
        tools=[get_time, calculate]
    )
    
    # Configure Claude with tools
    options = ClaudeAgentOptions(
        model="claude-haiku-4-5",
        mcp_servers={"tools": server},
        allowed_tools=["mcp__tools__get_time", "mcp__tools__calculate"],
        system_prompt="You are a helpful assistant with access to time and calculator tools."
    )
    
    # Use ClaudeSDKClient for more control
    async with ClaudeSDKClient(options=options) as client:
        print("\nTry asking me to:")
        print("- 'What time is it?'")
        print("- 'Calculate 2+2*3'")
        print("- 'What's 10*5?'")
        print("\nType 'quit' to exit")
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
            
            await client.query(user_input)
            
            print("Agent: ", end="", flush=True)
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            print(block.text, end="", flush=True)
            print()
    
    print("\n👋 Thanks for trying the agent!")


if __name__ == "__main__":
    asyncio.run(main())
