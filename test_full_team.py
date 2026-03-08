#!/usr/bin/env python3
"""
Test the full cc-team system
"""
import asyncio
import subprocess
import time
from pathlib import Path
from cc_team.team_manager import TeamManager
from cc_team.agent_spawner import AgentSpawner

async def test_full_team():
    """Test the complete team system"""
    print("🧪 Testing Full Team System")
    print("=" * 40)
    
    # Test team parsing
    print("\n1. Testing team parsing...")
    team_dir = Path("samples/team")
    team_manager = TeamManager(team_dir)
    agents = team_manager.parse_team_structure()
    
    print(f"✅ Found {len(agents)} agents:")
    for name, config in agents.items():
        print(f"   - {name}: {config.host}:{config.port}")
    
    # Test agent spawner
    print("\n2. Testing agent spawner...")
    spawner = AgentSpawner(team_manager)
    
    print("🚀 Starting all agents...")
    success = await spawner.start_all_agents()
    
    if success:
        print("✅ All agents started successfully!")
        
        # Show status
        print("\n3. Agent status:")
        status = spawner.get_agent_status()
        for name, info in status.items():
            running = "🟢" if info["running"] else "🔴"
            print(f"   {running} {name}: {info['host']}:{info['port']} (PID: {info['pid']})")
        
        print("\n4. Waiting for agents to fully start...")
        await asyncio.sleep(3)  # Give agents time to start
        
        print("5. Testing A2A communication...")
        await test_a2a_communication()
        
        print("\n5. Stopping agents...")
        await spawner.stop_all_agents()
        print("✅ All agents stopped")
        
    else:
        print("❌ Failed to start some agents")
    
    print("\n🎉 Full team test completed!")

async def test_a2a_communication():
    """Test A2A communication between agents"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        # Test Tom agent
        try:
            response = await client.get("http://localhost:8001/.well-known/agent.json")
            if response.status_code == 200:
                agent_card = response.json()
                print(f"   ✅ Tom agent card: {agent_card['name']}")
                
                # Send message to Tom
                message_data = {
                    "jsonrpc": "2.0",
                    "id": "test",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "messageId": "test-msg",
                            "role": "user",
                            "parts": [{"text": "Hello Tom!"}]
                        }
                    }
                }
                
                response = await client.post("http://localhost:8001/", json=message_data)
                if response.status_code == 200:
                    print("   ✅ Tom responded to message")
                else:
                    print(f"   ❌ Tom message failed: {response.status_code}")
            else:
                print(f"   ❌ Tom agent card failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Tom communication error: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_team())
