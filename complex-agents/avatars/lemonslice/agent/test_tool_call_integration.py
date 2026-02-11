"""
Integration test for tool call tracking with storage persistence.

This test verifies the complete flow:
1. Create a transcript with conversation turns and tool calls
2. Save the transcript to storage
3. Load the transcript from storage
4. Verify all data is preserved (turns and tool calls)
"""

import time
import tempfile
import shutil
from pathlib import Path

from scoring.models import ToolCall, RawTranscript, ConversationTurn
from scoring.storage import FilesystemStorage


def test_tool_call_persistence():
    """Test that tool calls are persisted and loaded correctly."""
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create storage backend
        storage = FilesystemStorage(temp_dir)
        
        # Create a sample transcript with turns and tool calls
        session_id = "test_session_with_tools"
        current_time = time.time()
        
        turns = [
            ConversationTurn(
                speaker="trainee",
                raw_text="Hello, I need to discuss the contract delay",
                normalized_text="Hello, I need to discuss the contract delay",
                timestamp=current_time,
                turn_index=0
            ),
            ConversationTurn(
                speaker="vendor",
                raw_text="Hi, yes we have a delay due to supplier issues",
                normalized_text="Hi, yes we have a delay due to supplier issues",
                timestamp=current_time + 5,
                turn_index=1
            ),
            ConversationTurn(
                speaker="trainee",
                raw_text="Can you provide that in writing?",
                normalized_text="Can you provide that in writing?",
                timestamp=current_time + 10,
                turn_index=2
            )
        ]
        
        tool_calls = [
            ToolCall(
                tool_name="how_am_i_doing",
                timestamp=current_time + 15,
                arguments={"check_type": "progress"},
                result="You're doing well! You requested written notice."
            ),
            ToolCall(
                tool_name="return_to_roleplay",
                timestamp=current_time + 20,
                arguments={},
                result=None
            )
        ]
        
        transcript = RawTranscript(
            session_id=session_id,
            scenario_id="scenario_1",
            session_start_time=current_time,
            session_end_time=current_time + 100,
            session_duration=100.0,
            participant_id="test_user_123",
            turns=turns,
            tool_calls=tool_calls
        )
        
        # Save the transcript
        save_path = storage.save_transcript(session_id, transcript)
        print(f"✓ Transcript saved to: {save_path}")
        
        # Verify the file exists
        assert Path(save_path).exists(), "Transcript file should exist"
        
        # Load the transcript
        loaded_transcript = storage.load_transcript(session_id)
        assert loaded_transcript is not None, "Should be able to load transcript"
        
        # Verify all fields are preserved
        assert loaded_transcript.session_id == session_id
        assert loaded_transcript.scenario_id == "scenario_1"
        assert loaded_transcript.participant_id == "test_user_123"
        assert loaded_transcript.session_duration == 100.0
        
        # Verify turns are preserved
        assert len(loaded_transcript.turns) == 3
        assert loaded_transcript.turns[0].speaker == "trainee"
        assert loaded_transcript.turns[0].raw_text == "Hello, I need to discuss the contract delay"
        assert loaded_transcript.turns[1].speaker == "vendor"
        assert loaded_transcript.turns[2].speaker == "trainee"
        
        # Verify tool calls are preserved
        assert len(loaded_transcript.tool_calls) == 2
        assert loaded_transcript.tool_calls[0].tool_name == "how_am_i_doing"
        assert loaded_transcript.tool_calls[0].arguments == {"check_type": "progress"}
        assert loaded_transcript.tool_calls[0].result == "You're doing well! You requested written notice."
        assert loaded_transcript.tool_calls[1].tool_name == "return_to_roleplay"
        assert loaded_transcript.tool_calls[1].arguments == {}
        assert loaded_transcript.tool_calls[1].result is None
        
        # Verify metadata includes tool_calls_count
        metadata = loaded_transcript.to_metadata()
        assert metadata["tool_calls_count"] == 2
        
        print("✓ Transcript loaded successfully")
        print(f"  - Session ID: {loaded_transcript.session_id}")
        print(f"  - Turns: {len(loaded_transcript.turns)}")
        print(f"  - Tool calls: {len(loaded_transcript.tool_calls)}")
        print(f"  - Tool call 1: {loaded_transcript.tool_calls[0].tool_name}")
        print(f"  - Tool call 2: {loaded_transcript.tool_calls[1].tool_name}")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print("✓ Cleaned up temporary directory")


def test_transcript_without_tool_calls():
    """Test that transcripts without tool calls still work (backward compatibility)."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        storage = FilesystemStorage(temp_dir)
        
        session_id = "test_session_no_tools"
        current_time = time.time()
        
        turns = [
            ConversationTurn(
                speaker="trainee",
                raw_text="Hello",
                normalized_text="Hello",
                timestamp=current_time,
                turn_index=0
            )
        ]
        
        # Create transcript with empty tool_calls list
        transcript = RawTranscript(
            session_id=session_id,
            scenario_id="scenario_1",
            session_start_time=current_time,
            session_end_time=current_time + 50,
            session_duration=50.0,
            participant_id="test_user",
            turns=turns,
            tool_calls=[]  # No tool calls
        )
        
        # Save and load
        storage.save_transcript(session_id, transcript)
        loaded_transcript = storage.load_transcript(session_id)
        
        # Verify
        assert loaded_transcript is not None
        assert len(loaded_transcript.turns) == 1
        assert len(loaded_transcript.tool_calls) == 0
        
        metadata = loaded_transcript.to_metadata()
        assert metadata["tool_calls_count"] == 0
        
        print("✓ Transcript without tool calls works correctly")
        print(f"  - Tool calls count: {metadata['tool_calls_count']}")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Running tool call integration tests...\n")
    
    try:
        test_tool_call_persistence()
        print()
        test_transcript_without_tool_calls()
        
        print("\n✅ All integration tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
