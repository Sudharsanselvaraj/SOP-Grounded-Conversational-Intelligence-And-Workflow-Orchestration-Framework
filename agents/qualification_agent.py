"""Lead qualification flow for capturing basic sales context."""

from __future__ import annotations

from collections.abc import Callable

from models.schemas import LeadData
from utils.logger import log_event


QUALIFICATION_QUESTIONS: list[tuple[str, str]] = [
    ("business_type", "Could I ask what type of business you are with?"),
    ("team_size", "Roughly how many people are on your team?"),
    ("current_tools", "What tools or software do you currently use?"),
]


def run_qualification(get_input_fn: Callable[[str], str]) -> LeadData:
    """Ask the qualification questions sequentially and return structured lead data."""

    lead: dict[str, str | None] = {
        "business_type": None,
        "team_size": None,
        "current_tools": None,
    }

    for field, question in QUALIFICATION_QUESTIONS:
        answer = get_input_fn(question).strip()
        lead[field] = answer or None

    lead_data = LeadData(**lead)
    log_event("lead_qualified", lead_data.model_dump())
    return lead_data
