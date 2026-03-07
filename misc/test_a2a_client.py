"""
Simple test client for the A2A agent
"""
import asyncio
import httpx
import json


async def test_a2a_agent():
    """Test the A2A agent endpoints"""
    base_url = "http://localhost:9999"
    
    print("🔧 Testing A2A Agent")
    print("=" * 40)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Get Agent Card
            print("\n1. Getting Agent Card...")
            response = await client.get(f"{base_url}/.well-known/agent.json")
            if response.status_code == 200:
                agent_card = response.json()
                print(f"   ✅ Agent: {agent_card.get('name')}")
                print(f"   📝 Description: {agent_card.get('description')}")
                print(f"   🏷️  Version: {agent_card.get('version')}")
                print(f"   🛠️  Skills: {len(agent_card.get('skills', []))}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                return
            
            # Test 2: Send Message (JSON-RPC format)
            print("\n2. Sending Message...")
            message_data = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "msg-1",
                        "role": "user",
                        "parts": [
                            {"text": "Hello! Can you introduce yourself?"}
                        ]
                    }
                }
            }
            
            response = await client.post(
                f"{base_url}/",
                json=message_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    result_data = result["result"]
                    # Handle message response
                    if result_data.get("kind") == "message":
                        for part in result_data.get("parts", []):
                            if "text" in part:
                                print(f"   🤖 Agent: {part['text']}")
                    # Handle task response  
                    elif result_data.get("kind") == "task":
                        print(f"   📋 Task ID: {result_data.get('id')}")
                        print(f"   📊 Status: {result_data.get('status', {}).get('state', 'unknown')}")
                    else:
                        print(f"   📄 Response: {result_data}")
                else:
                    print(f"   📄 Response: {result}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
            
            # Test 3: Send Calculator Request
            print("\n3. Testing Calculator...")
            calc_message = {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "msg-2",
                        "role": "user",
                        "parts": [
                            {"text": "Calculate 25 * 4"}
                        ]
                    }
                }
            }
            
            response = await client.post(
                f"{base_url}/",
                json=calc_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    result_data = result["result"]
                    if result_data.get("kind") == "message":
                        for part in result_data.get("parts", []):
                            if "text" in part:
                                print(f"   🧮 Result: {part['text']}")
                    else:
                        print(f"   📄 Response: {result_data}")
                else:
                    print(f"   📄 Response: {result}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
            
            # Test 4: List Tasks
            print("\n4. Listing Tasks...")
            tasks_request = {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "tasks/list",
                "params": {}
            }
            
            response = await client.post(
                f"{base_url}/",
                json=tasks_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    result_data = result["result"]
                    task_list = result_data.get("tasks", [])
                    print(f"   📋 Total tasks: {len(task_list)}")
                    for task in task_list:
                        print(f"   - {task.get('id')}: {task.get('status', {}).get('state', 'unknown')}")
                else:
                    print(f"   📄 Response: {result}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except httpx.ConnectError:
            print("❌ Cannot connect to agent server")
            print("💡 Make sure the agent is running:")
            print("   python3 simple_a2a_server.py")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_a2a_agent())
