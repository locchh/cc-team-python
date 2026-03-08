#!/usr/bin/env python3
"""
Quick test script for the cc-team system
"""
from pathlib import Path
from cc_team.team_manager import TeamManager

def test_team_parsing():
    """Test team directory parsing"""
    print("🧪 Testing team parsing...")
    
    team_dir = Path("samples/team")
    if not team_dir.exists():
        print("❌ Team directory not found")
        return False
    
    team_manager = TeamManager(team_dir)
    agents = team_manager.parse_team_structure()
    
    print(f"✅ Found {len(agents)} agents:")
    for name, config in agents.items():
        print(f"   - {name}: {config.host}:{config.port}")
        print(f"     Personality: {'✅' if config.personality else '❌'}")
        print(f"     Claude dir: {'✅' if (config.directory / '.claude').exists() else '❌'}")
    
    # Validate team
    issues = team_manager.validate_team()
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Team validation passed")
    
    return len(agents) > 0

if __name__ == "__main__":
    success = test_team_parsing()
    if success:
        print("\n🎉 Team parsing test passed!")
        print("💡 Next steps:")
        print("   1. Run: python3 dynamic_agent.py samples/team/tom")
        print("   2. Test A2A communication")
        print("   3. Run: cc-team samples/team")
    else:
        print("\n❌ Team parsing test failed!")
