"""Load and query SOP content used by the support workflow."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from config.settings import SOP_PATH


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9£]+", " ", text.lower())).strip()


@lru_cache(maxsize=1)
def load_sop() -> dict[str, Any]:
    """Load the SOP JSON once and cache it for the process lifetime."""

    with SOP_PATH.open(encoding="utf-8") as file_handle:
        return json.load(file_handle)


def sop_as_text() -> str:
    """Format the SOP as compact text for prompt injection."""

    sop = load_sop()
    business = sop["business"]
    hours = sop["hours"]
    services = sop["services"]
    booking = sop["booking"]
    escalation = sop["escalation_rules"]

    service_lines = []
    for service in services:
        if service["price_from"] == 0:
            price = "Free"
        else:
            price = f"from £{service['price_from']}"
        service_lines.append(f"- {service['name']}: {price}. {service['description']}")

    return "\n".join(
        [
            f"Business name: {business['name']}",
            f"Tagline: {business['tagline']}",
            f"Business hours: {hours['days']} {hours['open']} to {hours['close']}. Closed: {', '.join(hours['closed_days'])}.",
            "Services:",
            *service_lines,
            f"Booking channels: {', '.join(booking['channels'])}",
            f"Cancellation policy: {booking['cancellation_policy']}",
            "Escalation triggers: complaint, medical question, pricing negotiation, repeated unknown questions, or more than 2 unanswered questions.",
            f"Maximum unanswered before escalation: {escalation['max_unanswered_before_escalation']}",
        ]
    )


def _service_price_phrase(service_name: str, price_from: int) -> str:
    if price_from == 0:
        return f"{service_name} is free."
    if service_name.lower() == "botox":
        return f"Botox treatments start from £{price_from}."
    if service_name.lower() == "fillers":
        return f"Dermal fillers start from £{price_from}."
    return f"{service_name} starts from £{price_from}."


def match_sop_answer(question: str) -> dict[str, Any] | None:
    """Map a customer question to a known SOP answer using deterministic rules."""

    normalized = _normalize(question)
    sop = load_sop()
    business = sop["business"]
    hours = sop["hours"]
    services = sop["services"]
    booking = sop["booking"]

    if any(token in normalized for token in ("hours", "open", "opening", "when are you open", "what time do you open", "business hours")):
        answer = f"We're open {hours['days']} from {hours['open']} to {hours['close']}. We are closed on {', '.join(hours['closed_days'])}."
        return {
            "topic": "business_hours",
            "answer": answer,
            "confidence": 0.98,
            "sop_excerpt": f"Business hours: {hours['days']} {hours['open']} to {hours['close']}. Closed: {', '.join(hours['closed_days'])}.",
        }

    if "botox" in normalized and any(token in normalized for token in ("price", "cost", "how much", "pricing", "prices")):
        service = next(item for item in services if item["name"].lower() == "botox")
        answer = _service_price_phrase(service["name"], service["price_from"])
        return {
            "topic": "botox_pricing",
            "answer": answer,
            "confidence": 0.98,
            "sop_excerpt": f"{service['name']}: from £{service['price_from']}. {service['description']}",
        }

    if "filler" in normalized and any(token in normalized for token in ("price", "cost", "how much", "pricing", "prices")):
        service = next(item for item in services if item["name"].lower() == "fillers")
        answer = _service_price_phrase(service["name"], service["price_from"])
        return {
            "topic": "fillers_pricing",
            "answer": answer,
            "confidence": 0.98,
            "sop_excerpt": f"{service['name']}: from £{service['price_from']}. {service['description']}",
        }

    if any(token in normalized for token in ("free consultation", "consultation free", "do you offer consultations", "offer consultation")):
        service = next(item for item in services if item["name"].lower() == "free consultation")
        answer = "Yes. We offer a free consultation."
        return {
            "topic": "free_consultation",
            "answer": answer,
            "confidence": 0.97,
            "sop_excerpt": f"{service['name']}: Free. {service['description']}",
        }

    if any(token in normalized for token in ("what services do you offer", "what treatments do you offer", "services do you have", "treatments do you offer", "what do you offer")):
        answer = "We offer Botox starting from £200, Fillers starting from £250, and a free consultation."
        return {
            "topic": "services_overview",
            "answer": answer,
            "confidence": 0.95,
            "sop_excerpt": "Services: Botox from £200, Fillers from £250, Free Consultation.",
        }

    if any(token in normalized for token in ("book", "booking", "appointment", "reserve", "whatsapp", "website")):
        answer = "You can book via WhatsApp or our website."
        return {
            "topic": "booking_channels",
            "answer": answer,
            "confidence": 0.96,
            "sop_excerpt": f"Booking channels: {', '.join(booking['channels'])}.",
        }

    if any(token in normalized for token in ("cancel", "cancellation", "reschedule", "move my appointment", "change my appointment")):
        answer = "Our cancellation policy requires a minimum of 24 hours' notice."
        if not answer.endswith("."):
            answer = f"{answer}."
        return {
            "topic": "cancellation_policy",
            "answer": answer,
            "confidence": 0.97,
            "sop_excerpt": f"Cancellation policy: {booking['cancellation_policy']}",
        }

    if any(token in normalized for token in ("what is your business name", "clinic name", "name of your clinic", "what are you called")):
        answer = f"Our business name is {business['name']}."
        return {
            "topic": "business_name",
            "answer": answer,
            "confidence": 0.96,
            "sop_excerpt": f"Business name: {business['name']}",
        }

    return None
