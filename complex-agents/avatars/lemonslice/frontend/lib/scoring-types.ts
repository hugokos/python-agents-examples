/**
 * TypeScript interfaces for the post-scenario scoring system.
 * These match the Python dataclasses in agent/scoring/models.py
 */

export interface ConversationTurn {
  speaker: string; // "trainee" or "vendor"
  raw_text: string; // Original ASR output
  normalized_text: string; // Cleaned text for event extraction
  timestamp: number;
  turn_index: number;
}

export interface RawTranscript {
  session_id: string;
  scenario_id: string;
  session_start_time: number;
  session_end_time: number;
  session_duration: number;
  participant_id: string;
  turns: ConversationTurn[];
}

export interface NormalizedTranscript {
  session_id: string;
  turns: ConversationTurn[];
}

export enum EventType {
  ASK_FACTS = "ASK_FACTS",
  REQUEST_WRITTEN_NOTICE = "REQUEST_WRITTEN_NOTICE",
  PROPOSED_OPTION = "PROPOSED_OPTION",
  CONCESSION = "CONCESSION",
  CONSIDERATION = "CONSIDERATION",
  RISKY_COMMITMENT = "RISKY_COMMITMENT",
  CLOSEOUT = "CLOSEOUT",
}

export interface NegotiationEvent {
  event_type: EventType;
  speaker: string;
  timestamp: number;
  turn_index: number;
  quote: string;
  confidence: number; // 0.0-1.0
  char_start: number;
  char_end: number;
}

export interface Achievement {
  achievement_id: string;
  title: string;
  description: string;
  icon: string;
  timestamp: number;
  quote: string;
}

export interface ComboMoment {
  combo_type: "good" | "bad";
  title: string;
  description: string;
  event_sequence: NegotiationEvent[];
  timestamps: number[];
  quotes: string[];
  score_impact: number;
}

export interface ImprovementTip {
  priority: number; // 1-5
  action: string;
  evidence_quote: string;
  explanation: string;
}

export interface ScoreComposition {
  rubric_score: number;
  deterministic_caps: Array<{ rule: string; cap_value: number }>;
  deterministic_penalties: Array<{ rule: string; penalty_value: number }>;
  final_score: number;
}

export interface PrimaryStat {
  score: number;
  justification: string;
  composition: ScoreComposition;
}

export interface PrimaryStats {
  process_discipline: PrimaryStat;
  leverage_concession_control: PrimaryStat;
  information_gathering: PrimaryStat;
  outcome_quality: PrimaryStat;
  professionalism_relationship: PrimaryStat;
}

export interface ScoringMetadata {
  report_schema_version: string;
  scoring_version: string;
  models: {
    event_extraction: string;
    rubric_grading: string;
    tip_generation: string;
  };
  prompt_hashes: Record<string, string>;
  generated_at: number;
  rule_triggers: Array<{
    rule: string;
    reason: string;
    impact: Record<string, unknown>;
  }>;
}

export interface ScoringErrors {
  normalization_failed: boolean;
  event_extraction_failed: boolean;
  deterministic_scoring_failed: boolean;
  rubric_grading_failed: boolean;
  achievement_detection_failed: boolean;
  combo_detection_failed: boolean;
  tip_generation_failed: boolean;
  error_messages: string[];
}

export interface SessionMetadata {
  session_id: string;
  scenario_id: string;
  session_start_time: number;
  session_end_time: number;
  session_duration: number;
  participant_id: string;
}

export interface AfterActionReport {
  session_metadata: SessionMetadata;
  primary_stats: PrimaryStats;
  letter_grade: string;
  achievements: Achievement[];
  combo_moments: ComboMoment[];
  improvement_tips: ImprovementTip[];
  raw_transcript: RawTranscript;
  normalized_transcript: NormalizedTranscript;
  extracted_events: NegotiationEvent[];
  scoring_metadata: ScoringMetadata;
  errors: ScoringErrors;
}
