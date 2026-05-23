"""FAQ agent that answers only from SOP-grounded knowledge."""

from __future__ import annotations

import json

from openai import OpenAI

from config.settings import MAX_TOKENS, MODEL, OPENAI_API_KEY, PROMPTS_DIR, TEMPERATURE
from models.schemas import FAQResponse
from utils.logger import log_event, log_turn
from utils.sop_loader import match_sop_answer, sop_as_text


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _load_prompt() -> str:
    return (PROMPTS_DIR / "faq_system_prompt.txt").read_text(encoding="utf-8")


def _safe_unavailable_answer() -> str:
    return (
        "I’m sorry, I don’t have that information in the current SOP, so I can’t confirm it reliably. "
        "I’ll connect you with a member of our team who can help."
    )


def _build_response_from_match(question: str, match: dict[str, object]) -> FAQResponse:
    candidate_answer = str(match["answer"])
    source_excerpt = str(match["sop_excerpt"])
    system_prompt = _load_prompt().format(
        sop_text=sop_as_text(),
        source_excerpt=source_excerpt,
        candidate_answer=candidate_answer,
    )

    try:
        if client is None:
            raise RuntimeError("OpenAI client unavailable")

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        faq_response = FAQResponse(**parsed)
    except Exception:
        faq_response = FAQResponse(
            answer=candidate_answer,
            confidence=float(match["confidence"]),
            source_found=True,
            requires_escalation=False,
        )
    else:
        faq_response = FAQResponse(
            answer=candidate_answer,
            confidence=max(float(match["confidence"]), float(faq_response.confidence)),
            source_found=True,
            requires_escalation=False,
        )

    return faq_response


def answer(question: str) -> FAQResponse:
    """Answer a customer question using SOP-only grounding."""

    match = match_sop_answer(question)
    if match is None:
        response = FAQResponse(
            answer=_safe_unavailable_answer(),
            confidence=0.15,
            source_found=False,
            requires_escalation=True,
        )
        log_turn(
            user_message=question,
            ai_response=response.answer,
            confidence=response.confidence,
            escalation_reason="SOP gap",
        )
        log_event("faq_sop_gap", {"question": question})
        return response

    response = _build_response_from_match(question, match)
    log_turn(
        user_message=question,
        ai_response=response.answer,
        confidence=response.confidence,
        escalation_reason=None,
    )
    log_event("faq_answered", {"question": question, "topic": match["topic"]})
    return response
