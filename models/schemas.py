"""Pydantic schemas shared across the Closira AI workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FAQResponse(BaseModel):
    """Structured FAQ output."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(..., description="Answer grounded in SOP only")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    source_found: bool = Field(..., description="Whether the SOP contains the answer")
    requires_escalation: bool = Field(..., description="Whether the message should be escalated")


class LeadData(BaseModel):
    """Lead qualification data captured during conversation."""

    model_config = ConfigDict(extra="forbid")

    business_type: str | None = None
    team_size: str | None = None
    current_tools: str | None = None


class EscalationResult(BaseModel):
    """Escalation decision output."""

    model_config = ConfigDict(extra="forbid")

    escalate: bool
    reason: str


class ConversationSummary(BaseModel):
    """End-of-session report."""

    model_config = ConfigDict(extra="forbid")

    customer_intent: str
    questions_asked: list[str] = Field(default_factory=list)
    lead_information: LeadData = Field(default_factory=LeadData)
    sop_gaps: list[str] = Field(default_factory=list)
    escalations: list[str] = Field(default_factory=list)
    recommended_next_action: str
    conversation_status: Literal["Completed", "Escalated", "Incomplete"]


class ConversationTurn(BaseModel):
    """Single turn in the conversation history."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str
