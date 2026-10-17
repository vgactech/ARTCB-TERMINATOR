"""
conftest.py — ARTCB TERMINATOR FORENSIC
R090 — Fix rate_limiter state leaking between tests.

The slowapi Limiter uses a shared in-memory storage keyed by remote address
("testclient" in TestClient runs).  When tests that hit rate-limited routes
(e.g. /api/llm-attack/stream @ 6/min) run sequentially, later tests receive
HTTP 429 even though the per-test intent is independent.

Fix: an autouse session-scoped fixture resets the Limiter storage before every
test that uses the TestClient, preventing counter accumulation across the suite.
"""
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Reset the shared slowapi Limiter storage before each test."""
    from guardian_api.app import limiter  # noqa: PLC0415
    limiter.reset()
