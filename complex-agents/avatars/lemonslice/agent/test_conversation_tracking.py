"""
Simple test to verify conversation turn tracking in BaseVendorAgent.

This test verifies that:
1. UserData has a conversation_turns field
2. The conversation_turns list is initialized as empty
3. Turns can be added to the list with the correct structure
"""

import time
import sys
from pathlib import Path

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly from the file
import importlib.util
spec = importlib.util.spec_from_file_location("lemonslice_agent", Path(__file__).parent / "lemonslice-agent.py")
lemonslice_agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lemonslice_agent)

UserData = lemonslice_agent.UserData


def test_userdata_has_conversation_turns():
    """Test that UserData has conversation_turns field."""
    userdata = UserData()
    assert hasattr(userdata, 'conversation_turns'), "UserData should have conversation_turns field"
    assert isinstance(userdata.conversation_turns, list), "conversation_turns should be a list"
    assert len(userdata.conversation_turns) == 0, "conversation_turns should be empty initially"
    print("✓ UserData has conversation_turns field")


def test_conversation_turn_structure():
    """Test that conversation turns have the correct structure."""
    userdata = UserData()
    
    # Simulate adding a user turn
    user_turn = {
        "speaker": "trainee",
        "raw_text": "Hello, this is a test message",
        "timestamp": time.time(),
        "turn_index": 0
    }
    userdata.conversation_turns.append(user_turn)
    
    # Simulate adding an agent turn
    agent_turn = {
        "speaker": "vendor",
        "raw_text": "Hi, I'm the vendor agent",
        "timestamp": time.time(),
        "turn_index": 1
    }
    userdata.conversation_turns.append(agent_turn)
    
    # Verify structure
    assert len(userdata.conversation_turns) == 2, "Should have 2 turns"
    
    # Check user turn
    assert userdata.conversation_turns[0]["speaker"] == "trainee"
    assert userdata.conversation_turns[0]["raw_text"] == "Hello, this is a test message"
    assert "timestamp" in userdata.conversation_turns[0]
    assert userdata.conversation_turns[0]["turn_index"] == 0
    
    # Check agent turn
    assert userdata.conversation_turns[1]["speaker"] == "vendor"
    assert userdata.conversation_turns[1]["raw_text"] == "Hi, I'm the vendor agent"
    assert "timestamp" in userdata.conversation_turns[1]
    assert userdata.conversation_turns[1]["turn_index"] == 1
    
    print("✓ Conversation turns have correct structure")
    print(f"  - User turn: {userdata.conversation_turns[0]['raw_text'][:30]}...")
    print(f"  - Agent turn: {userdata.conversation_turns[1]['raw_text'][:30]}...")


def test_conversation_turns_ordering():
    """Test that conversation turns maintain chronological order."""
    userdata = UserData()
    
    # Add multiple turns
    for i in range(5):
        turn = {
            "speaker": "trainee" if i % 2 == 0 else "vendor",
            "raw_text": f"Turn {i}",
            "timestamp": time.time(),
            "turn_index": i
        }
        userdata.conversation_turns.append(turn)
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    # Verify ordering
    assert len(userdata.conversation_turns) == 5
    for i in range(5):
        assert userdata.conversation_turns[i]["turn_index"] == i
        if i > 0:
            assert userdata.conversation_turns[i]["timestamp"] >= userdata.conversation_turns[i-1]["timestamp"]
    
    print("✓ Conversation turns maintain chronological order")


if __name__ == "__main__":
    print("Running conversation tracking tests...\n")
    
    try:
        test_userdata_has_conversation_turns()
        test_conversation_turn_structure()
        test_conversation_turns_ordering()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
