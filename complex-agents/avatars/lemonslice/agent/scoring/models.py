"""Core data models for the post-scenario scoring system."""

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional


@dataclass
class ToolCall:
    """A function tool invocation during the session."""
    tool_name: str  # Name of the function tool
    timestamp: float  # When the tool was called
    arguments: dict  # Arguments passed to the tool
    result: Optional[str] = None  # Result returned by the tool (if any)


@dataclass
class ConversationTurn:
    """A single turn in the conversation transcript."""
    speaker: str  # "trainee" or "vendor"
    raw_text: str  # Original ASR output (never modified)
    normalized_text: str  # Cleaned text for event extraction
    timestamp: float
    turn_index: int


@dataclass
class RawTranscript:
    """Complete conversation record from a LiveKit session."""
    session_id: str
    scenario_id: str
    session_start_time: float
    session_end_time: float
    session_duration: float
    participant_id: str
    turns: list[ConversationTurn]
    tool_calls: list[ToolCall] = field(default_factory=list)  # Function tool invocations
    
    def to_metadata(self) -> dict:
        """Extract session metadata for the After Action Report."""
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "session_start_time": self.session_start_time,
            "session_end_time": self.session_end_time,
            "session_duration": self.session_duration,
            "participant_id": self.participant_id,
            "tool_calls_count": len(self.tool_calls)
        }


@dataclass
class NormalizedTranscript:
    """Transcript with normalized text for better event extraction."""
    session_id: str
    turns: list[ConversationTurn]  # Same structure, but normalized_text is cleaned


class EventType(Enum):
    """Types of negotiation events that can be extracted from transcripts."""
    ASK_FACTS = "ASK_FACTS"  # Trainee requests contract information
    REQUEST_WRITTEN_NOTICE = "REQUEST_WRITTEN_NOTICE"  # Trainee asks for written documentation
    PROPOSED_OPTION = "PROPOSED_OPTION"  # Either party proposes a solution
    CONCESSION = "CONCESSION"  # Either party gives something up
    CONSIDERATION = "CONSIDERATION"  # Trainee requests something in exchange
    RISKY_COMMITMENT = "RISKY_COMMITMENT"  # Trainee makes verbal promises
    CLOSEOUT = "CLOSEOUT"  # Negotiation reaches conclusion


@dataclass
class NegotiationEvent:
    """A structured representation of a specific action in the conversation."""
    event_type: EventType
    speaker: str
    timestamp: float
    turn_index: int
    quote: str  # Verbatim excerpt from transcript
    confidence: float  # 0.0-1.0
    char_start: int  # Character offset in turn text
    char_end: int  # Character offset in turn text


@dataclass
class Achievement:
    """A badge awarded for demonstrating specific negotiation behaviors."""
    achievement_id: str
    title: str
    description: str
    icon: str
    timestamp: float
    quote: str  # Evidence from transcript


@dataclass
class ComboMoment:
    """A sequence of events that receives a score multiplier."""
    combo_type: str  # "good" or "bad"
    title: str
    description: str
    event_sequence: list[NegotiationEvent]
    timestamps: list[float]
    quotes: list[str]
    score_impact: int


@dataclass
class ImprovementTip:
    """An actionable recommendation with supporting evidence."""
    priority: int  # 1-5
    action: str  # Specific action to take
    evidence_quote: str  # Quote showing missed opportunity
    explanation: str  # Why this action matters


@dataclass
class ScoreComposition:
    """Detailed breakdown of how a score was calculated."""
    rubric_score: int
    deterministic_caps: list[dict]  # [{rule: str, cap_value: int}]
    deterministic_penalties: list[dict]  # [{rule: str, penalty_value: int}]
    final_score: int


@dataclass
class ScoringMetadata:
    """Provenance and versioning information for the scoring run."""
    report_schema_version: str = "1.0"
    scoring_version: str = "1.0"
    models: dict = field(default_factory=lambda: {
        "event_extraction": "gpt-4o",
        "rubric_grading": "gpt-4o",
        "tip_generation": "gpt-4o"
    })
    prompt_hashes: dict = field(default_factory=dict)  # {step: hash}
    generated_at: float = field(default_factory=time.time)
    rule_triggers: list[dict] = field(default_factory=list)  # [{rule: str, reason: str, impact: dict}]


@dataclass
class ScoringErrors:
    """Flags indicating which steps failed during scoring."""
    normalization_failed: bool = False
    event_extraction_failed: bool = False
    deterministic_scoring_failed: bool = False
    rubric_grading_failed: bool = False
    achievement_detection_failed: bool = False
    combo_detection_failed: bool = False
    tip_generation_failed: bool = False
    error_messages: list[str] = field(default_factory=list)


@dataclass
class AfterActionReport:
    """Complete scoring analysis generated after a scenario completes."""
    session_metadata: dict
    primary_stats: dict[str, dict]  # {stat_name: {score: int, justification: str, composition: ScoreComposition}}
    letter_grade: str
    achievements: list[Achievement]
    combo_moments: list[ComboMoment]
    improvement_tips: list[ImprovementTip]
    raw_transcript: RawTranscript
    normalized_transcript: NormalizedTranscript
    extracted_events: list[NegotiationEvent]
    scoring_metadata: ScoringMetadata
    errors: ScoringErrors
    
    def to_json(self) -> str:
        """Serialize to JSON for frontend consumption."""
        return json.dumps({
            "session_metadata": self.session_metadata,
            "primary_stats": {
                stat_name: {
                    "score": stat_data["score"],
                    "justification": stat_data["justification"],
                    "composition": {
                        "rubric_score": stat_data["composition"].rubric_score,
                        "deterministic_caps": stat_data["composition"].deterministic_caps,
                        "deterministic_penalties": stat_data["composition"].deterministic_penalties,
                        "final_score": stat_data["composition"].final_score
                    }
                }
                for stat_name, stat_data in self.primary_stats.items()
            },
            "letter_grade": self.letter_grade,
            "achievements": [asdict(a) for a in self.achievements],
            "combo_moments": [
                {
                    "combo_type": c.combo_type,
                    "title": c.title,
                    "description": c.description,
                    "timestamps": c.timestamps,
                    "quotes": c.quotes,
                    "score_impact": c.score_impact,
                    "event_sequence": [
                        {
                            "event_type": e.event_type.value,
                            "speaker": e.speaker,
                            "timestamp": e.timestamp,
                            "turn_index": e.turn_index,
                            "quote": e.quote,
                            "confidence": e.confidence,
                            "char_start": e.char_start,
                            "char_end": e.char_end
                        }
                        for e in c.event_sequence
                    ]
                }
                for c in self.combo_moments
            ],
            "improvement_tips": [asdict(t) for t in self.improvement_tips],
            "raw_transcript": {
                "session_id": self.raw_transcript.session_id,
                "scenario_id": self.raw_transcript.scenario_id,
                "session_start_time": self.raw_transcript.session_start_time,
                "session_end_time": self.raw_transcript.session_end_time,
                "session_duration": self.raw_transcript.session_duration,
                "participant_id": self.raw_transcript.participant_id,
                "turns": [asdict(turn) for turn in self.raw_transcript.turns],
                "tool_calls": [asdict(tc) for tc in self.raw_transcript.tool_calls]
            },
            "normalized_transcript": {
                "session_id": self.normalized_transcript.session_id,
                "turns": [asdict(turn) for turn in self.normalized_transcript.turns]
            },
            "extracted_events": [
                {
                    "event_type": e.event_type.value,
                    "speaker": e.speaker,
                    "timestamp": e.timestamp,
                    "turn_index": e.turn_index,
                    "quote": e.quote,
                    "confidence": e.confidence,
                    "char_start": e.char_start,
                    "char_end": e.char_end
                }
                for e in self.extracted_events
            ],
            "scoring_metadata": asdict(self.scoring_metadata),
            "errors": asdict(self.errors)
        }, indent=2)
