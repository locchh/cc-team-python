"""
Minimal Agent Example
Just the basics to understand Claude SDK
"""
import asyncio
from claude_agent_sdk import query


async def main():
    print("🤖 Minimal Claude Agent Demo")
    print("=" * 40)
    
    # Simple one-liner query
    print("\n1. Simple Query:")
    async for message in query(prompt="Say hello in one sentence"):
        print(f"   {message}")
    
    # Interactive chat
    print("\n2. Interactive Chat (type 'quit' to exit):")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        
        print("Agent: ", end="", flush=True)
        async for message in query(prompt=user_input):
            print(message, end="", flush=True)
        print()
    
    print("\n👋 Thanks for chatting!")


if __name__ == "__main__":
    asyncio.run(main())
