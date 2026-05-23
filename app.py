"""Interactive CLI entry point for the Closira AI workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich import box
from rich.console import Console
from rich.panel import Panel

from agents import escalation_agent, faq_agent, qualification_agent, summary_agent
from config.settings import OPENAI_API_KEY, ensure_directories
from models.schemas import ConversationTurn, EscalationResult, LeadData
from utils.logger import log_event


console = Console()

BANNER = """
[bold magenta]╔══════════════════════════════════════════╗[/]
[bold magenta]║   Bloom Aesthetics Clinic · AI Support   ║[/]
[bold magenta]╚══════════════════════════════════════════╝[/]
[dim]Powered by Closira[/]
"""

ESCALATION_MESSAGE = (
    "I’m going to connect you with one of our human team members who will be better placed to help you. "
    "Please bear with us — someone will be in touch shortly."
)


def _print_ai(text: str) -> None:
    console.print(f"\n[bold cyan]Bloom AI:[/] {text}\n")


def _print_system(text: str) -> None:
    console.print(f"[dim italic]{text}[/]")


def _get_user_input(prompt: str | None = None) -> str:
    if prompt:
        _print_ai(prompt)
    try:
        return console.input("[bold yellow]Customer:[/] ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Session interrupted.[/]")
        raise SystemExit(0) from None


def _format_summary(summary: object) -> str:
    if hasattr(summary, "model_dump"):
        return json.dumps(summary.model_dump(), indent=2, ensure_ascii=False)
    return json.dumps(summary, indent=2, ensure_ascii=False)  # type: ignore[arg-type]


def run() -> None:
    ensure_directories()
    console.print(BANNER)
    if not OPENAI_API_KEY:
        _print_system("OPENAI_API_KEY is not set. The workflow will fall back to deterministic safety behavior where needed.")

    history: list[ConversationTurn] = []
    lead_data: LeadData | None = None
    escalations: list[str] = []
    sop_gaps: list[str] = []
    unanswered_count = 0
    qualification_completed = False

    _print_ai(
        "Welcome to Bloom Aesthetics Clinic. I can help with our services, pricing, bookings, and cancellation policy. How can I help today?"
    )

    while True:
        user_input = _get_user_input()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye", "goodbye"}:
            break

        history.append(ConversationTurn(role="user", content=user_input))
        faq_result = faq_agent.answer(user_input)

        if not faq_result.source_found:
            sop_gaps.append(user_input)
            unanswered_count += 1
        else:
            unanswered_count = 0

        escalation_result = escalation_agent.check(
            message=user_input,
            confidence=faq_result.confidence,
            unanswered_count=unanswered_count,
        )

        if faq_result.requires_escalation and not escalation_result.escalate:
            escalation_result = EscalationResult(
                escalate=True,
                reason="FAQ agent flagged escalation",
            )

        _print_ai(faq_result.answer)
        history.append(ConversationTurn(role="assistant", content=faq_result.answer))
        _print_system(f"Confidence: {faq_result.confidence:.0%}")

        if escalation_result.escalate:
            escalations.append(escalation_result.reason)
            _print_ai(ESCALATION_MESSAGE)
            _print_system(f"Escalation logged: {escalation_result.reason}")
            log_event(
                "escalation_handoff",
                {
                    "reason": escalation_result.reason,
                    "message": user_input,
                    "unanswered_count": unanswered_count,
                },
            )
            break

        if not qualification_completed and faq_result.source_found:
            _print_ai("Before I let you go, may I ask a few quick questions?")

            def _qualification_input(prompt_text: str) -> str:
                history.append(ConversationTurn(role="assistant", content=prompt_text))
                return _get_user_input(prompt_text)

            lead_data = qualification_agent.run_qualification(_qualification_input)
            qualification_completed = True
            _print_ai("Thank you. Is there anything else I can help you with?")
            history.append(ConversationTurn(role="assistant", content="Thank you. Is there anything else I can help you with?"))

    console.print()
    console.rule("[bold magenta]Generating Conversation Summary[/]")
    console.print()

    summary = summary_agent.generate(
        history=history,
        lead_data=lead_data,
        escalations=escalations,
        sop_gaps=sop_gaps,
    )

    console.print(
        Panel(
            _format_summary(summary),
            title="[bold cyan]Session Summary[/]",
            border_style="magenta",
            box=box.ROUNDED,
        )
    )


if __name__ == "__main__":
    run()
