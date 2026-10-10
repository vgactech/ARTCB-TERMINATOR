"""FastAPI bridge between the web interface and the Guardian demo engine."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from guardian_mcp.demo_scenario import DemoReport, run_demo_scenario


app = FastAPI(
    title="ARTCB TERMINATOR API",
    description="Guardian Security Console demonstration API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _to_json_value(value: Any) -> Any:
    """Convert Guardian dataclasses and enums into JSON-safe values."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _to_json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_value(item) for item in value]
    return value


def serialize_report(report: DemoReport) -> dict[str, Any]:
    """Expose the demo report with an explicit frontend-friendly summary."""
    payload = _to_json_value(report)
    payload["overall_verdict"] = "GO" if report.is_go() else "NO_GO"
    payload["protected"] = bool(report.blocking and report.blocking.is_valid())
    payload["tampering_detected"] = bool(
        report.replay_r0_tampered
        and report.replay_r0_tampered.verdict == "FAIL"
    )
    return payload


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "artcb-terminator-api",
        "engine": "guardian",
    }


@app.post("/api/simulation/run")
def run_simulation() -> dict[str, Any]:
    return serialize_report(run_demo_scenario())
