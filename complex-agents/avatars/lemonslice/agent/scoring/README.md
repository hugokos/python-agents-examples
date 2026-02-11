# Post-Scenario Scoring System

This directory contains the implementation of the post-scenario scoring and feedback system for the procurement negotiation training application.

## Directory Structure

```
scoring/
├── __init__.py              # Package exports
├── models.py                # Core data models (dataclasses)
├── config.py                # Configuration management
├── README.md                # This file
│
├── capture.py               # Transcript capture (to be implemented)
├── normalizer.py            # Transcript normalization (to be implemented)
├── event_extractor.py       # Event extraction with OpenAI (to be implemented)
├── deterministic_scorer.py  # Deterministic scoring rules (to be implemented)
├── rubric_grader.py         # Rubric grading with OpenAI (to be implemented)
├── achievement_detector.py  # Achievement detection (to be implemented)
├── combo_detector.py        # Combo moment detection (to be implemented)
├── tip_generator.py         # Improvement tip generation (to be implemented)
├── orchestrator.py          # Scoring pipeline orchestration (to be implemented)
└── storage.py               # Storage layer (filesystem/S3) (to be implemented)
```

## Core Data Models

All data models are defined in `models.py`:

- **ConversationTurn**: A single turn in the conversation
- **RawTranscript**: Complete conversation record from LiveKit
- **NormalizedTranscript**: Transcript with cleaned text
- **EventType**: Enum of negotiation event types
- **NegotiationEvent**: Structured representation of a negotiation action
- **Achievement**: Badge for demonstrating best practices
- **ComboMoment**: Sequence of events with score multiplier
- **ImprovementTip**: Actionable recommendation with evidence
- **ScoreComposition**: Breakdown of score calculation
- **ScoringMetadata**: Provenance and versioning info
- **ScoringErrors**: Flags for failed scoring steps
- **AfterActionReport**: Complete scoring analysis

## Configuration

Configuration is managed through environment variables (see `.env.example`):

- `OPENAI_API_KEY`: Required for event extraction and rubric grading
- `STORAGE_TYPE`: Storage backend (filesystem, s3, r2)
- `STORAGE_PATH`: Local path for filesystem storage
- S3/R2 configuration (optional, for cloud storage)

## Usage

```python
from scoring import AfterActionReport, RawTranscript
from scoring.config import get_config

# Load configuration
config = get_config()

# Create a transcript (example)
transcript = RawTranscript(
    session_id="session_123",
    scenario_id="scenario_1",
    session_start_time=1705334400.0,
    session_end_time=1705334580.0,
    session_duration=180.0,
    participant_id="user_xyz",
    turns=[...]
)

# Run scoring (to be implemented)
# report = await run_scoring_job(transcript)
# print(report.to_json())
```

## Testing

Property-based tests are located in `tests/` and use the `hypothesis` library.

## Design Documentation

See `.kiro/specs/post-scenario-scoring/` for complete requirements and design documentation.
