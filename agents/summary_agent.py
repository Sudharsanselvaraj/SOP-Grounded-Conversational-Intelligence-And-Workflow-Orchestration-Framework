"""Summary agent that turns the session into a structured report."""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any

from openai import OpenAI

from config.settings import MAX_TOKENS, MODEL, OPENAI_API_KEY, PROMPTS_DIR
from models.schemas import ConversationSummary, ConversationTurn, LeadData
from utils.logger import log_event


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _load_prompt() -> str:
    return (PROMPTS_DIR / "summary_prompt.txt").read_text(encoding="utf-8")


def _format_history(history: list[ConversationTurn]) -> str:
    return "\n".join(f"{turn.role.title()}: {turn.content}" for turn in history)


def _extract_questions(history: list[ConversationTurn]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()
    for turn in history:
        if turn.role != "user":
            continue
        candidate = turn.content.strip()
        if not candidate:
            continue
        if candidate.endswith("?") or candidate.lower().startswith(("what ", "how ", "when ", "can ", "do you", "is there", "may i")):
            if candidate not in seen:
                questions.append(candidate)
                seen.add(candidate)
    return questions


def _infer_intent(questions: list[str], sop_gaps: list[str], escalations: list[str]) -> str:
    if escalations:
        return "Customer required escalation during the support conversation"
    if any("price" in question.lower() for question in questions):
        return "Customer asked about pricing and booking details"
    if any("cancel" in question.lower() for question in questions):
        return "Customer asked about the cancellation policy"
    if sop_gaps:
        return "Customer asked about information not covered in the SOP"
    return "General support enquiry"


def _fallback_summary(
    history: list[ConversationTurn],
    lead_data: LeadData | None,
    escalations: list[str],
    sop_gaps: list[str],
) -> ConversationSummary:
    questions = _extract_questions(history)
    status = "Escalated" if escalations else "Completed" if history else "Incomplete"
    next_action = (
        "Review the escalation and respond with a human agent." if escalations else
        "Follow up with the customer and offer the next best step from the SOP."
    )
    lead_information = lead_data or LeadData()
    return ConversationSummary(
        customer_intent=_infer_intent(questions, sop_gaps, escalations),
        questions_asked=questions,
        lead_information=lead_information,
        sop_gaps=list(OrderedDict.fromkeys(sop_gaps)),
        escalations=list(OrderedDict.fromkeys(escalations)),
        recommended_next_action=next_action,
        conversation_status=status,
    )


def generate(
    history: list[ConversationTurn],
    lead_data: LeadData | None,
    escalations: list[str],
    sop_gaps: list[str],
) -> ConversationSummary:
    """Generate the final structured report for the conversation."""

    questions_asked = _extract_questions(history)
    lead_information = lead_data or LeadData()
    prompt = _load_prompt().format(
        conversation_history=_format_history(history),
        lead_data=json.dumps(lead_information.model_dump(), ensure_ascii=False),
        escalations=json.dumps(list(OrderedDict.fromkeys(escalations)), ensure_ascii=False),
        sop_gaps=json.dumps(list(OrderedDict.fromkeys(sop_gaps)), ensure_ascii=False),
        questions_asked=json.dumps(questions_asked, ensure_ascii=False),
    )

    try:
        if client is None:
            raise RuntimeError("OpenAI client unavailable")

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.0,
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        payload: dict[str, Any] = json.loads(raw)
        if isinstance(payload.get("lead_information"), dict):
            payload["lead_information"] = LeadData(**payload["lead_information"])
        summary = ConversationSummary(**payload)
    except Exception:
        summary = _fallback_summary(history, lead_data, escalations, sop_gaps)
    else:
        if not summary.questions_asked:
            summary = summary.model_copy(update={"questions_asked": questions_asked})
        if not summary.lead_information:
            summary = summary.model_copy(update={"lead_information": lead_information})

    log_event("summary_generated", summary.model_dump())
    return summary
