"""Hybrid escalation detection using rules first and an LLM fallback."""

from __future__ import annotations

import json
import re

from openai import OpenAI

from config.settings import LOW_CONFIDENCE_THRESHOLD, MODEL, OPENAI_API_KEY, PROMPTS_DIR, UNANSWERED_ESCALATION_THRESHOLD
from models.schemas import EscalationResult
from utils.logger import log_event


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

_COMPLAINT_PATTERNS = re.compile(
    r"\b(unhappy|dissatisfied|terrible|awful|horrible|furious|angry|upset|complaint|complain|refund|unacceptable|appalling)\b",
    re.IGNORECASE,
)
_NEGATIVE_SENTIMENT_PATTERNS = re.compile(
    r"\b(disappointed|frustrated|annoyed|not happy|fed up|bad experience|poor service|rude)\b",
    re.IGNORECASE,
)
_HUMAN_REQUEST_PATTERNS = re.compile(
    r"\b(human|manager|supervisor|real person|speak to someone|talk to a person|agent|transfer me|call me back)\b",
    re.IGNORECASE,
)
_MEDICAL_PATTERNS = re.compile(
    r"\b(pregnant|pregnancy|breastfeeding|allergy|allergic|medication|contraindication|safe for|health risk|side effect|medical|doctor|nurse|blood thinners|numbing|anaesthesia)\b",
    re.IGNORECASE,
)
_PRICING_NEG_PATTERNS = re.compile(
    r"\b(discount|cheaper|negotiate|deal|lower the price|reduce the price|price match|too expensive|can you do better|best price|offer lower)\b",
    re.IGNORECASE,
)


def _load_prompt() -> str:
    return (PROMPTS_DIR / "escalation_prompt.txt").read_text(encoding="utf-8")


def _rule_based_check(message: str, confidence: float | None, unanswered_count: int) -> EscalationResult | None:
    """Apply deterministic escalation rules before the LLM check."""

    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
        return EscalationResult(escalate=True, reason="Low confidence detected")
    if unanswered_count > UNANSWERED_ESCALATION_THRESHOLD:
        return EscalationResult(escalate=True, reason="Repeated unknown questions")
    if _COMPLAINT_PATTERNS.search(message):
        return EscalationResult(escalate=True, reason="Complaint detected")
    if _NEGATIVE_SENTIMENT_PATTERNS.search(message):
        return EscalationResult(escalate=True, reason="Negative sentiment detected")
    if _HUMAN_REQUEST_PATTERNS.search(message):
        return EscalationResult(escalate=True, reason="Human request detected")
    if _MEDICAL_PATTERNS.search(message):
        return EscalationResult(escalate=True, reason="Medical question detected")
    if _PRICING_NEG_PATTERNS.search(message):
        return EscalationResult(escalate=True, reason="Pricing negotiation detected")
    return None


def _llm_check(message: str, confidence: float | None, unanswered_count: int) -> EscalationResult:
    """Use the model to catch subtle escalation signals."""

    prompt = _load_prompt().format(
        message=message,
        confidence="null" if confidence is None else confidence,
        unanswered_count=unanswered_count,
    )
    if client is None:
        raise RuntimeError("OpenAI client unavailable")

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        temperature=0.0,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or '{"escalate": false, "reason": ""}'
    payload = json.loads(raw)
    return EscalationResult(**payload)


def check(
    message: str,
    confidence: float | None = None,
    unanswered_count: int = 0,
) -> EscalationResult:
    """Return the final escalation decision for the latest customer message."""

    rule_result = _rule_based_check(message, confidence, unanswered_count)
    if rule_result is not None:
        log_event("escalation_triggered", rule_result.model_dump())
        return rule_result

    try:
        llm_result = _llm_check(message, confidence, unanswered_count)
    except Exception:
        llm_result = EscalationResult(escalate=False, reason="")

    if llm_result.escalate:
        log_event("escalation_triggered", llm_result.model_dump())
    return llm_result
