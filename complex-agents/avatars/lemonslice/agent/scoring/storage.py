"""Storage layer for transcripts and scoring reports."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import ScoringConfig, get_config
from .models import AfterActionReport, RawTranscript


class StorageBackend:
    """Base class for storage backends."""
    
    def save_transcript(self, session_id: str, transcript: RawTranscript) -> str:
        """Save a raw transcript and return the storage path."""
        raise NotImplementedError
    
    def load_transcript(self, session_id: str) -> Optional[RawTranscript]:
        """Load a raw transcript by session ID."""
        raise NotImplementedError
    
    def save_report(self, session_id: str, report: AfterActionReport) -> str:
        """Save an After Action Report and return the storage path."""
        raise NotImplementedError
    
    def load_report(self, session_id: str) -> Optional[AfterActionReport]:
        """Load an After Action Report by session ID."""
        raise NotImplementedError


class FilesystemStorage(StorageBackend):
    """Filesystem-based storage backend."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.transcripts_dir = self.base_path / "transcripts"
        self.reports_dir = self.base_path / "reports"
        
        # Create directories if they don't exist
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_date_dir(self, timestamp: float) -> Path:
        """Get the date-based directory for organizing files."""
        date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        return Path(date_str)
    
    def save_transcript(self, session_id: str, transcript: RawTranscript) -> str:
        """Save a raw transcript to filesystem."""
        date_dir = self._get_date_dir(transcript.session_start_time)
        full_dir = self.transcripts_dir / date_dir
        full_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = full_dir / f"{session_id}_raw.json"
        
        # Convert to JSON
        transcript_dict = {
            "session_id": transcript.session_id,
            "scenario_id": transcript.scenario_id,
            "session_start_time": transcript.session_start_time,
            "session_end_time": transcript.session_end_time,
            "session_duration": transcript.session_duration,
            "participant_id": transcript.participant_id,
            "turns": [
                {
                    "speaker": turn.speaker,
                    "raw_text": turn.raw_text,
                    "normalized_text": turn.normalized_text,
                    "timestamp": turn.timestamp,
                    "turn_index": turn.turn_index
                }
                for turn in transcript.turns
            ],
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "timestamp": tc.timestamp,
                    "arguments": tc.arguments,
                    "result": tc.result
                }
                for tc in transcript.tool_calls
            ]
        }
        
        with open(file_path, "w") as f:
            json.dump(transcript_dict, f, indent=2)
        
        return str(file_path)
    
    def load_transcript(self, session_id: str) -> Optional[RawTranscript]:
        """Load a raw transcript from filesystem."""
        # Search for the transcript file (we don't know the date)
        for date_dir in self.transcripts_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            file_path = date_dir / f"{session_id}_raw.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                from .models import ConversationTurn, ToolCall
                
                return RawTranscript(
                    session_id=data["session_id"],
                    scenario_id=data["scenario_id"],
                    session_start_time=data["session_start_time"],
                    session_end_time=data["session_end_time"],
                    session_duration=data["session_duration"],
                    participant_id=data["participant_id"],
                    turns=[
                        ConversationTurn(
                            speaker=turn["speaker"],
                            raw_text=turn["raw_text"],
                            normalized_text=turn["normalized_text"],
                            timestamp=turn["timestamp"],
                            turn_index=turn["turn_index"]
                        )
                        for turn in data["turns"]
                    ],
                    tool_calls=[
                        ToolCall(
                            tool_name=tc["tool_name"],
                            timestamp=tc["timestamp"],
                            arguments=tc["arguments"],
                            result=tc.get("result")
                        )
                        for tc in data.get("tool_calls", [])
                    ]
                )
        
        return None
    
    def save_report(self, session_id: str, report: AfterActionReport) -> str:
        """Save an After Action Report to filesystem."""
        date_dir = self._get_date_dir(report.session_metadata["session_start_time"])
        full_dir = self.reports_dir / date_dir
        full_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = full_dir / f"{session_id}_report.json"
        
        with open(file_path, "w") as f:
            f.write(report.to_json())
        
        return str(file_path)
    
    def load_report(self, session_id: str) -> Optional[AfterActionReport]:
        """Load an After Action Report from filesystem."""
        # Search for the report file (we don't know the date)
        for date_dir in self.reports_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            file_path = date_dir / f"{session_id}_report.json"
            if file_path.exists():
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                # Note: Full deserialization would require reconstructing all dataclasses
                # For now, we return the raw JSON data
                # TODO: Implement full deserialization if needed
                return data  # type: ignore
        
        return None


# Global storage instance
_storage: Optional[StorageBackend] = None


def get_storage(config: Optional[ScoringConfig] = None) -> StorageBackend:
    """Get the global storage backend instance."""
    global _storage
    
    if _storage is None:
        if config is None:
            config = get_config()
        
        if config.storage_type == "filesystem":
            _storage = FilesystemStorage(config.storage_path)
        elif config.storage_type in ["s3", "r2"]:
            # TODO: Implement S3/R2 storage backend
            raise NotImplementedError("S3/R2 storage not yet implemented")
        else:
            raise ValueError(f"Unknown storage type: {config.storage_type}")
    
    return _storage


def set_storage(storage: StorageBackend) -> None:
    """Set the global storage backend instance (for testing)."""
    global _storage
    _storage = storage
