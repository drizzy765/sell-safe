"""Demo seed is idempotent and refuses production without a flag."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed_demo import main, seed_memory  # noqa: E402

from app.config import Settings  # noqa: E402


def test_seed_memory_is_idempotent() -> None:
    settings = Settings(llm_provider="groq", pii_salt="demo-salt")
    first = seed_memory(settings)
    second = seed_memory(settings)
    assert first["business_name"] == "Tolu's Bags"
    assert first["product_count"] == 4
    assert second["product_count"] == 4
    assert first["daily_summary_demo"]["label"] == "demo"


def test_main_memory_exits_zero() -> None:
    assert main(["--memory"]) == 0
