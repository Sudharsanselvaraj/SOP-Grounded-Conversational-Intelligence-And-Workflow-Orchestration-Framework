"""Application settings for the Closira AI workflow."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
LOG_DIR = BASE_DIR / "logs"

SOP_PATH = DATA_DIR / "sop.json"
LOG_PATH = LOG_DIR / "conversation.log"

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
MODEL: str = os.getenv("MODEL", "gpt-4.1-mini")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))

UNANSWERED_ESCALATION_THRESHOLD: int = int(os.getenv("UNANSWERED_ESCALATION_THRESHOLD", "2"))
LOW_CONFIDENCE_THRESHOLD: float = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.5"))


def ensure_directories() -> None:
	"""Create runtime directories when the application starts."""

	DATA_DIR.mkdir(parents=True, exist_ok=True)
	PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
	LOG_DIR.mkdir(parents=True, exist_ok=True)
