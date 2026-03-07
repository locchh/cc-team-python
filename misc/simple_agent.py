"""
Simple Agent using Claude SDK
A single script to run a basic agent
"""
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def run_simple_agent():
    """Run a simple agent with Claude SDK"""
    
    print("🤖 Starting Simple Agent...")
    
    # Basic query
    print("\n--- Basic Query ---")
    async for message in query(prompt="Hello! What can you help me with?"):
        print(f"Claude: {message}")
    
    # Query with options
    print("\n--- Query with Options ---")
    options = ClaudeAgentOptions(
        model="claude-haiku-4-5",
        system_prompt="You are a helpful assistant that specializes in explaining concepts clearly.",
        max_turns=1
    )
    
    async for message in query(prompt="Explain what an AI agent is in simple terms", options=options):
        print(f"Claude: {message}")
    
    # Interactive mode
    print("\n--- Interactive Mode ---")
    print("Type 'quit' to exit")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
            
        print("Claude: ", end="", flush=True)
        async for message in query(prompt=user_input):
            print(message, end="", flush=True)
        print()  # New line after response


if __name__ == "__main__":
    asyncio.run(run_simple_agent())
