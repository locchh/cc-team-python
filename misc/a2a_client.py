#!/usr/bin/env python3
"""
Simple A2A client to interact with team agents
Usage: python3 misc/a2a_client.py samples/team
Then enter messages in the format: agent_name: message
Example: tom: What's 2 + 2?
"""

import asyncio
import sys
from pathlib import Path
import httpx
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from cc_team.team_manager import TeamManager


class A2AClient:
    """Simple A2A client for team agents"""

    def __init__(self, team_manager: TeamManager):
        self.team_manager = team_manager
        self.agents = team_manager.get_agent_configs()
        self.message_counter = 0

    async def send_message(self, agent_name: str, text: str) -> str:
        """Send a message to an agent and return response"""
        if agent_name not in self.agents:
            return f"❌ Agent '{agent_name}' not found"

        agent = self.agents[agent_name]
        url = f"http://{agent.host}:{agent.port}/"
        self.message_counter += 1

        # Build A2A request
        request_data = {
            "jsonrpc": "2.0",
            "id": str(self.message_counter),
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"msg-{self.message_counter}",
                    "role": "user",
                    "parts": [{"text": text}],
                }
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url, json=request_data, headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        result_data = result["result"]
                        if result_data.get("kind") == "message":
                            texts = []
                            for part in result_data.get("parts", []):
                                if "text" in part:
                                    texts.append(part["text"])
                            if texts:
                                return "\n".join(texts)
                            else:
                                return f"[Empty response from {agent_name}]"
                        else:
                            return str(result_data)
                    else:
                        return str(result)
                else:
                    return f"❌ Error {response.status_code}: {response.text[:200]}"

        except httpx.ConnectError:
            return f"❌ Cannot connect to {agent_name} at {agent.host}:{agent.port}"
        except asyncio.TimeoutError:
            return f"⏱️  Timeout waiting for response from {agent_name}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def interactive_chat(self) -> None:
        """Run interactive chat with agents"""
        print("\n" + "=" * 60)
        print("🤖 A2A Team Chat Client")
        print("=" * 60)
        print(f"\n✅ Available agents: {', '.join(sorted(self.agents.keys()))}")
        print("\n📝 Format: agent_name: message")
        print("   Example: tom: What can you help with?")
        print("   Type 'quit' or 'exit' to quit\n")

        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit"]:
                    print("👋 Goodbye!")
                    break

                if ":" not in user_input:
                    print("❌ Invalid format. Use: agent_name: message")
                    continue

                agent_name, message = user_input.split(":", 1)
                agent_name = agent_name.strip()
                message = message.strip()

                if not message:
                    print("❌ Message cannot be empty")
                    continue

                print(f"\n📤 Sending to {agent_name}...")
                response = await self.send_message(agent_name, message)
                print(f"📥 Response from {agent_name}:\n{response}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 a2a_client.py <team_directory>")
        print("Example: python3 a2a_client.py samples/team")
        return

    team_dir = Path(sys.argv[1])

    if not team_dir.exists():
        print(f"❌ Team directory not found: {team_dir}")
        return

    try:
        # Load team
        tm = TeamManager(team_dir)
        tm.parse_team_structure()

        if not tm.get_agent_configs():
            print("❌ No agents found in team")
            return

        # Start client
        client = A2AClient(tm)
        await client.interactive_chat()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
