"""Configuration for the post-scenario scoring system."""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class ScoringConfig:
    """Configuration for the scoring system."""
    
    # OpenAI API configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.3
    
    # Storage configuration
    storage_type: Literal["filesystem", "s3", "r2"] = "filesystem"
    storage_path: str = "./data"
    
    # S3/R2 configuration (optional)
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    
    # Scoring thresholds
    event_confidence_threshold: float = 0.55
    min_fact_questions_base: int = 3
    
    # Retry configuration
    max_retries: int = 3
    retry_backoff_base: float = 1.0  # seconds
    
    @classmethod
    def from_env(cls) -> "ScoringConfig":
        """Load configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
            storage_type=os.getenv("STORAGE_TYPE", "filesystem"),  # type: ignore
            storage_path=os.getenv("STORAGE_PATH", "./data"),
            s3_bucket=os.getenv("S3_BUCKET", ""),
            s3_region=os.getenv("S3_REGION", "us-east-1"),
            s3_access_key=os.getenv("S3_ACCESS_KEY", ""),
            s3_secret_key=os.getenv("S3_SECRET_KEY", ""),
            event_confidence_threshold=float(os.getenv("EVENT_CONFIDENCE_THRESHOLD", "0.55")),
            min_fact_questions_base=int(os.getenv("MIN_FACT_QUESTIONS_BASE", "3")),
            max_retries=int(os.getenv("SCORING_MAX_RETRIES", "3")),
            retry_backoff_base=float(os.getenv("SCORING_RETRY_BACKOFF", "1.0")),
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        if self.storage_type not in ["filesystem", "s3", "r2"]:
            errors.append(f"Invalid STORAGE_TYPE: {self.storage_type}")
        
        if self.storage_type in ["s3", "r2"]:
            if not self.s3_bucket:
                errors.append("S3_BUCKET is required for S3/R2 storage")
            if not self.s3_access_key:
                errors.append("S3_ACCESS_KEY is required for S3/R2 storage")
            if not self.s3_secret_key:
                errors.append("S3_SECRET_KEY is required for S3/R2 storage")
        
        if self.event_confidence_threshold < 0 or self.event_confidence_threshold > 1:
            errors.append("EVENT_CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        if self.openai_temperature < 0 or self.openai_temperature > 2:
            errors.append("OPENAI_TEMPERATURE must be between 0 and 2")
        
        return errors


# Global configuration instance
_config: ScoringConfig | None = None


def get_config() -> ScoringConfig:
    """Get the global scoring configuration instance."""
    global _config
    if _config is None:
        _config = ScoringConfig.from_env()
        errors = _config.validate()
        if errors:
            raise ValueError(f"Invalid scoring configuration: {', '.join(errors)}")
    return _config


def set_config(config: ScoringConfig) -> None:
    """Set the global scoring configuration instance (for testing)."""
    global _config
    _config = config
