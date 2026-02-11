"""
Test to verify function tool call tracking in BaseVendorAgent.

This test verifies that:
1. UserData has a tool_calls field
2. The tool_calls list is initialized as empty
3. Tool calls can be added to the list with the correct structure
4. Tool calls are properly serialized in RawTranscript
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

# Import scoring models
from scoring.models import ToolCall, RawTranscript, ConversationTurn


def test_userdata_has_tool_calls():
    """Test that UserData has tool_calls field."""
    userdata = UserData()
    assert hasattr(userdata, 'tool_calls'), "UserData should have tool_calls field"
    assert isinstance(userdata.tool_calls, list), "tool_calls should be a list"
    assert len(userdata.tool_calls) == 0, "tool_calls should be empty initially"
    print("✓ UserData has tool_calls field")


def test_tool_call_structure():
    """Test that tool calls have the correct structure."""
    userdata = UserData()
    
    # Simulate adding a tool call
    tool_call = {
        "tool_name": "how_am_i_doing",
        "timestamp": time.time(),
        "arguments": {"check_type": "progress"},
        "result": "You're doing well!"
    }
    userdata.tool_calls.append(tool_call)
    
    # Simulate adding another tool call
    tool_call2 = {
        "tool_name": "return_to_roleplay",
        "timestamp": time.time(),
        "arguments": {},
        "result": None
    }
    userdata.tool_calls.append(tool_call2)
    
    # Verify structure
    assert len(userdata.tool_calls) == 2, "Should have 2 tool calls"
    
    # Check first tool call
    assert userdata.tool_calls[0]["tool_name"] == "how_am_i_doing"
    assert "timestamp" in userdata.tool_calls[0]
    assert userdata.tool_calls[0]["arguments"] == {"check_type": "progress"}
    assert userdata.tool_calls[0]["result"] == "You're doing well!"
    
    # Check second tool call
    assert userdata.tool_calls[1]["tool_name"] == "return_to_roleplay"
    assert "timestamp" in userdata.tool_calls[1]
    assert userdata.tool_calls[1]["arguments"] == {}
    assert userdata.tool_calls[1]["result"] is None
    
    print("✓ Tool calls have correct structure")
    print(f"  - Tool call 1: {userdata.tool_calls[0]['tool_name']}")
    print(f"  - Tool call 2: {userdata.tool_calls[1]['tool_name']}")


def test_tool_call_model():
    """Test that ToolCall dataclass works correctly."""
    tool_call = ToolCall(
        tool_name="how_am_i_doing",
        timestamp=time.time(),
        arguments={"check_type": "progress"},
        result="You're doing well!"
    )
    
    assert tool_call.tool_name == "how_am_i_doing"
    assert tool_call.arguments == {"check_type": "progress"}
    assert tool_call.result == "You're doing well!"
    assert isinstance(tool_call.timestamp, float)
    
    print("✓ ToolCall dataclass works correctly")


def test_raw_transcript_with_tool_calls():
    """Test that RawTranscript includes tool_calls."""
    # Create a sample transcript with tool calls
    turns = [
        ConversationTurn(
            speaker="trainee",
            raw_text="Hello",
            normalized_text="Hello",
            timestamp=time.time(),
            turn_index=0
        ),
        ConversationTurn(
            speaker="vendor",
            raw_text="Hi there",
            normalized_text="Hi there",
            timestamp=time.time(),
            turn_index=1
        )
    ]
    
    tool_calls = [
        ToolCall(
            tool_name="how_am_i_doing",
            timestamp=time.time(),
            arguments={"check_type": "progress"},
            result="You're doing well!"
        )
    ]
    
    transcript = RawTranscript(
        session_id="test_session_123",
        scenario_id="scenario_1",
        session_start_time=time.time(),
        session_end_time=time.time() + 100,
        session_duration=100.0,
        participant_id="test_user",
        turns=turns,
        tool_calls=tool_calls
    )
    
    # Verify transcript structure
    assert len(transcript.turns) == 2
    assert len(transcript.tool_calls) == 1
    assert transcript.tool_calls[0].tool_name == "how_am_i_doing"
    
    # Verify metadata includes tool_calls_count
    metadata = transcript.to_metadata()
    assert "tool_calls_count" in metadata
    assert metadata["tool_calls_count"] == 1
    
    print("✓ RawTranscript includes tool_calls")
    print(f"  - Turns: {len(transcript.turns)}")
    print(f"  - Tool calls: {len(transcript.tool_calls)}")
    print(f"  - Metadata tool_calls_count: {metadata['tool_calls_count']}")


def test_tool_calls_chronological_order():
    """Test that tool calls maintain chronological order."""
    userdata = UserData()
    
    # Add multiple tool calls
    for i in range(3):
        tool_call = {
            "tool_name": f"tool_{i}",
            "timestamp": time.time(),
            "arguments": {"index": i},
            "result": None
        }
        userdata.tool_calls.append(tool_call)
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    # Verify ordering
    assert len(userdata.tool_calls) == 3
    for i in range(3):
        assert userdata.tool_calls[i]["tool_name"] == f"tool_{i}"
        if i > 0:
            assert userdata.tool_calls[i]["timestamp"] >= userdata.tool_calls[i-1]["timestamp"]
    
    print("✓ Tool calls maintain chronological order")


if __name__ == "__main__":
    print("Running tool call tracking tests...\n")
    
    try:
        test_userdata_has_tool_calls()
        test_tool_call_structure()
        test_tool_call_model()
        test_raw_transcript_with_tool_calls()
        test_tool_calls_chronological_order()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
