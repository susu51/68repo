"""
AI Settings Models for Panel-Aware AI Assistant
Defines settings structure for OpenAI integration, redaction rules, and rate limiting
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class RedactionRule(BaseModel):
    """Individual redaction rule configuration"""
    type: str = Field(..., description="Type: phone, email, iban, jwt, address, card")
    enabled: bool = Field(default=True, description="Whether this rule is active")
    pattern: Optional[str] = Field(None, description="Custom regex pattern (optional)")


class AISettings(BaseModel):
    """AI Diagnostics Panel Settings"""
    id: str = Field(default="ai_settings_default", description="Settings document ID")
    
    # OpenAI Integration
    openai_api_key: Optional[str] = Field(None, description="Custom OpenAI API key (overrides Emergent LLM Key)")
    use_emergent_key: bool = Field(default=True, description="Use Emergent LLM Key if no custom key provided")
    default_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    
    # Time Window Settings
    default_time_window_minutes: int = Field(default=60, description="Default time window for queries")
    
    # Rate Limiting
    rate_limit_per_min: int = Field(default=6, description="AI queries per minute per admin")
    
    # Redaction Rules
    redact_rules: List[RedactionRule] = Field(
        default_factory=lambda: [
            RedactionRule(type="phone", enabled=True),
            RedactionRule(type="email", enabled=True),
            RedactionRule(type="iban", enabled=True),
            RedactionRule(type="jwt", enabled=True),
            RedactionRule(type="address", enabled=True),
            RedactionRule(type="card", enabled=True),
        ],
        description="PII redaction rules"
    )
    
    # Metadata
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Field(None, description="Admin user ID who last updated")


class AISettingsUpdate(BaseModel):
    """Model for updating AI settings"""
    openai_api_key: Optional[str] = None
    use_emergent_key: Optional[bool] = None
    default_model: Optional[str] = None
    default_time_window_minutes: Optional[int] = None
    rate_limit_per_min: Optional[int] = None
    redact_rules: Optional[List[RedactionRule]] = None


class AISettingsResponse(BaseModel):
    """Response model for AI settings (masks sensitive keys)"""
    id: str
    openai_api_key_configured: bool = Field(description="Whether custom API key is set (masked)")
    use_emergent_key: bool
    default_model: str
    default_time_window_minutes: int
    rate_limit_per_min: int
    redact_rules: List[RedactionRule]
    updated_at: datetime
    updated_by: Optional[str] = None
