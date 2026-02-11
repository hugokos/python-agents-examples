"""Unit tests for transcript persistence functionality."""

import os
import tempfile
import time
import uuid
from pathlib import Path

from scoring.models import ConversationTurn, RawTranscript, ToolCall
from scoring.storage import FilesystemStorage


def test_persist_and_load_transcript():
    """Test that a transcript can be persisted and loaded back."""
    # Create a temporary directory for storage
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FilesystemStorage(tmpdir)
        
        # Create a sample transcript
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        scenario_id = "scenario_1"
        session_start_time = time.time()
        session_end_time = session_start_time + 180.0
        participant_id = "test_participant"
        
        turns = [
            ConversationTurn(
                speaker="trainee",
                raw_text="Hello, this is a test.",
                normalized_text="Hello, this is a test.",
                timestamp=session_start_time + 1.0,
                turn_index=0
            ),
            ConversationTurn(
                speaker="vendor",
                raw_text="Hi, how can I help you?",
                normalized_text="Hi, how can I help you?",
                timestamp=session_start_time + 3.0,
                turn_index=1
            ),
            ConversationTurn(
                speaker="trainee",
                raw_text="I need information about the contract.",
                normalized_text="I need information about the contract.",
                timestamp=session_start_time + 5.0,
                turn_index=2
            )
        ]
        
        tool_calls = [
            ToolCall(
                tool_name="how_am_i_doing",
                timestamp=session_start_time + 10.0,
                arguments={},
                result="You're doing great!"
            )
        ]
        
        transcript = RawTranscript(
            session_id=session_id,
            scenario_id=scenario_id,
            session_start_time=session_start_time,
            session_end_time=session_end_time,
            session_duration=180.0,
            participant_id=participant_id,
            turns=turns,
            tool_calls=tool_calls
        )
        
        # Persist the transcript
        storage_path = storage.save_transcript(session_id, transcript)
        print(f"✓ Transcript persisted to: {storage_path}")
        
        # Verify the file was created
        assert Path(storage_path).exists(), "Storage file should exist"
        print(f"✓ Storage file exists")
        
        # Load the transcript back
        loaded_transcript = storage.load_transcript(session_id)
        
        # Verify all fields match
        assert loaded_transcript is not None, "Loaded transcript should not be None"
        assert loaded_transcript.session_id == session_id
        assert loaded_transcript.scenario_id == scenario_id
        assert loaded_transcript.session_start_time == session_start_time
        assert loaded_transcript.session_end_time == session_end_time
        assert loaded_transcript.session_duration == 180.0
        assert loaded_transcript.participant_id == participant_id
        print(f"✓ All metadata fields match")
        
        # Verify turns
        assert len(loaded_transcript.turns) == 3, "Should have 3 turns"
        for i, turn in enumerate(loaded_transcript.turns):
            assert turn.speaker == turns[i].speaker
            assert turn.raw_text == turns[i].raw_text
            assert turn.normalized_text == turns[i].normalized_text
            assert turn.timestamp == turns[i].timestamp
            assert turn.turn_index == turns[i].turn_index
        print(f"✓ All {len(turns)} turns match")
        
        # Verify tool calls
        assert len(loaded_transcript.tool_calls) == 1, "Should have 1 tool call"
        assert loaded_transcript.tool_calls[0].tool_name == "how_am_i_doing"
        assert loaded_transcript.tool_calls[0].timestamp == tool_calls[0].timestamp
        assert loaded_transcript.tool_calls[0].result == "You're doing great!"
        print(f"✓ Tool calls match")
        
        print("\n✓ test_persist_and_load_transcript PASSED")


def test_persist_transcript_with_no_tool_calls():
    """Test persisting a transcript with no tool calls."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FilesystemStorage(tmpdir)
        
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session_start_time = time.time()
        
        transcript = RawTranscript(
            session_id=session_id,
            scenario_id="scenario_1",
            session_start_time=session_start_time,
            session_end_time=session_start_time + 60.0,
            session_duration=60.0,
            participant_id="test_participant",
            turns=[
                ConversationTurn(
                    speaker="trainee",
                    raw_text="Test message",
                    normalized_text="Test message",
                    timestamp=session_start_time + 1.0,
                    turn_index=0
                )
            ],
            tool_calls=[]  # No tool calls
        )
        
        # Persist and load
        storage.save_transcript(session_id, transcript)
        loaded_transcript = storage.load_transcript(session_id)
        
        # Verify
        assert loaded_transcript is not None
        assert len(loaded_transcript.tool_calls) == 0
        print("✓ test_persist_transcript_with_no_tool_calls PASSED")


def test_persist_transcript_with_empty_turns():
    """Test persisting a transcript with no conversation turns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FilesystemStorage(tmpdir)
        
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        session_start_time = time.time()
        
        transcript = RawTranscript(
            session_id=session_id,
            scenario_id="scenario_1",
            session_start_time=session_start_time,
            session_end_time=session_start_time + 10.0,
            session_duration=10.0,
            participant_id="test_participant",
            turns=[],  # No turns
            tool_calls=[]
        )
        
        # Persist and load
        storage.save_transcript(session_id, transcript)
        loaded_transcript = storage.load_transcript(session_id)
        
        # Verify
        assert loaded_transcript is not None
        assert len(loaded_transcript.turns) == 0
        print("✓ test_persist_transcript_with_empty_turns PASSED")


def test_load_nonexistent_transcript():
    """Test loading a transcript that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FilesystemStorage(tmpdir)
        
        # Try to load a non-existent transcript
        loaded_transcript = storage.load_transcript("nonexistent_session")
        
        # Should return None
        assert loaded_transcript is None
        print("✓ test_load_nonexistent_transcript PASSED")


def test_session_metadata_extraction():
    """Test that session metadata can be extracted from transcript."""
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_start_time = time.time()
    
    transcript = RawTranscript(
        session_id=session_id,
        scenario_id="scenario_1",
        session_start_time=session_start_time,
        session_end_time=session_start_time + 180.0,
        session_duration=180.0,
        participant_id="test_participant",
        turns=[],
        tool_calls=[
            ToolCall(
                tool_name="test_tool",
                timestamp=session_start_time + 10.0,
                arguments={},
                result=None
            )
        ]
    )
    
    # Extract metadata
    metadata = transcript.to_metadata()
    
    # Verify metadata
    assert metadata["session_id"] == session_id
    assert metadata["scenario_id"] == "scenario_1"
    assert metadata["session_start_time"] == session_start_time
    assert metadata["session_end_time"] == session_start_time + 180.0
    assert metadata["session_duration"] == 180.0
    assert metadata["participant_id"] == "test_participant"
    assert metadata["tool_calls_count"] == 1
    print("✓ test_session_metadata_extraction PASSED")


if __name__ == "__main__":
    print("Running transcript persistence tests...\n")
    
    try:
        test_persist_and_load_transcript()
        test_persist_transcript_with_no_tool_calls()
        test_persist_transcript_with_empty_turns()
        test_load_nonexistent_transcript()
        test_session_metadata_extraction()
        
        print("\n" + "="*50)
        print("ALL TESTS PASSED ✓")
        print("="*50)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise

