"""Tests for the liveness / hand-movement challenge (C-KYC liveness gate)."""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from guardian_api.app import app
from guardian_api.liveness import (
    FAIL,
    GESTURES,
    PASS,
    SIMULATED,
    LivenessController,
    LivenessObservation,
    liveness_controller,
)
from guardian_mcp.instrumentation import GENESIS_HASH

client = TestClient(app)


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    event_type: str | None = None
    for line in text.splitlines():
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and event_type is not None:
            events.append((event_type, json.loads(line.split(":", 1)[1].strip())))
            event_type = None
    return events


def _matching_observation(gesture: str) -> dict:
    return {
        "gesture": gesture,
        "hand_frames": 999,
        "movement_score": 1.0,
        "directions": ["left", "right"],
        "pinch_ratio": 0.1,
        "gesture_matched": True,
        "duration_ms": 1500,
    }


# ─── Unit: controller ─────────────────────────────────────────────────────────


def test_status_reports_enabled_and_gestures() -> None:
    controller = LivenessController()
    status = controller.status()
    assert status["enabled"] is True
    assert status["ttl_seconds"] >= 5
    ids = {g["id"] for g in status["gestures"]}
    assert ids == set(GESTURES)


def test_new_challenge_is_unique_single_use() -> None:
    controller = LivenessController()
    first = controller.new_challenge()
    second = controller.new_challenge()
    assert first["challenge_id"] != second["challenge_id"]
    assert first["nonce"] != second["nonce"]
    assert first["gesture"] in GESTURES
    assert first["simulated"] is False


def test_verify_pass_records_chained_evidence() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(**_matching_observation(challenge["gesture"])),
    )
    assert result.liveness == PASS
    assert result.human_proven is True
    assert result.guardian_event_id
    assert controller.event_count() == 1

    events = controller.get_all_events()
    assert events[0][0].previous_event_hash == GENESIS_HASH
    assert events[0][0].compute_hash() == events[0][1]


def test_verify_replay_is_rejected() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    observation = LivenessObservation(**_matching_observation(challenge["gesture"]))
    assert controller.verify(
        challenge_id=challenge["challenge_id"], nonce=challenge["nonce"], observation=observation
    ).liveness == PASS
    replay = controller.verify(
        challenge_id=challenge["challenge_id"], nonce=challenge["nonce"], observation=observation
    )
    assert replay.liveness == FAIL
    assert "replay" in replay.reason
    assert replay.evidence_id is not None


def test_verify_bad_nonce_fails() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce="deadbeef",
        observation=LivenessObservation(**_matching_observation(challenge["gesture"])),
    )
    assert result.liveness == FAIL
    assert "nonce" in result.reason


def test_verify_unknown_challenge_fails() -> None:
    controller = LivenessController()
    result = controller.verify(
        challenge_id="does-not-exist",
        nonce="x",
        observation=LivenessObservation(gesture="left_to_right"),
    )
    assert result.liveness == FAIL


def test_verify_expired_challenge_fails() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    internal = controller._challenges[challenge["challenge_id"]]  # noqa: SLF001
    internal.expires_at = time.time() - 1
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(**_matching_observation(challenge["gesture"])),
    )
    assert result.liveness == FAIL
    assert "expir" in result.reason


@pytest.mark.parametrize(
    ("field", "value", "needle"),
    [
        ("gesture", "not_a_gesture", "conforme"),
        ("gesture_matched", False, "non détecté"),
        ("hand_frames", 0, "court"),
        ("movement_score", 0.0, "amplitude"),
    ],
)
def test_verify_weak_observations_fail(field: str, value: object, needle: str) -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    observation = _matching_observation(challenge["gesture"])
    observation[field] = value
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(**observation),
    )
    assert result.liveness == FAIL
    assert needle in result.reason


def test_simulated_flag_records_allow_without_human_proof() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(gesture=challenge["gesture"]),
        simulated=True,
    )
    assert result.liveness == SIMULATED
    assert result.human_proven is False
    assert result.data_source == "SIMULATED"


def test_disabled_env_issues_simulated_challenge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUARDIAN_LIVENESS_ENABLED", "false")
    controller = LivenessController()
    challenge = controller.new_challenge()
    assert challenge["simulated"] is True
    result = controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(gesture=challenge["gesture"]),
    )
    assert result.liveness == SIMULATED
    assert result.human_proven is False


def test_result_for_returns_stored_result() -> None:
    controller = LivenessController()
    challenge = controller.new_challenge()
    controller.verify(
        challenge_id=challenge["challenge_id"],
        nonce=challenge["nonce"],
        observation=LivenessObservation(**_matching_observation(challenge["gesture"])),
    )
    stored = controller.result_for(challenge["challenge_id"])
    assert stored is not None
    assert stored.liveness == PASS
    assert controller.result_for("unknown") is None


# ─── API ──────────────────────────────────────────────────────────────────────


def test_api_status() -> None:
    response = client.get("/api/liveness/status")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_api_challenge_and_verify_pass() -> None:
    challenge = client.post("/api/liveness/challenge").json()
    body = _matching_observation(challenge["gesture"])
    body.update({"challenge_id": challenge["challenge_id"], "nonce": challenge["nonce"]})
    result = client.post("/api/liveness/verify", json=body).json()
    assert result["liveness"] == PASS
    assert result["human_proven"] is True


def test_api_verify_fail_gives_evidence_id() -> None:
    challenge = client.post("/api/liveness/challenge").json()
    body = _matching_observation("not_a_gesture")
    body.update({"challenge_id": challenge["challenge_id"], "nonce": challenge["nonce"]})
    result = client.post("/api/liveness/verify", json=body).json()
    assert result["liveness"] == FAIL
    assert result["evidence_id"].startswith("evidence:")


# ─── KYC integration ──────────────────────────────────────────────────────────


def _verified_token(gesture_override: str | None = None) -> str:
    challenge = liveness_controller.new_challenge()
    body = _matching_observation(gesture_override or challenge["gesture"])
    body.update({"challenge_id": challenge["challenge_id"], "nonce": challenge["nonce"]})
    client.post("/api/liveness/verify", json=body)
    return challenge["challenge_id"]


def test_kyc_with_passed_liveness_approves() -> None:
    token = _verified_token()
    response = client.get(f"/api/kyc/stream?voice=false&liveness_token={token}")
    events = _parse_sse(response.text)
    liveness = [d for t, d in events if t == "liveness_check"]
    assert liveness and liveness[0]["status"] == PASS
    assert liveness[0]["human_proven"] is True
    result = [d for t, d in events if t == "kyc_result"][0]
    assert result["verdict"] == "APPROVED"
    assert result["human_proven"] is True


def test_kyc_with_failed_liveness_rejects() -> None:
    token = _verified_token(gesture_override="not_a_gesture")
    response = client.get(f"/api/kyc/stream?voice=false&liveness_token={token}")
    events = _parse_sse(response.text)
    liveness = [d for t, d in events if t == "liveness_check"]
    assert liveness and liveness[0]["status"] == FAIL
    result = [d for t, d in events if t == "kyc_result"][0]
    assert result["verdict"] == "REJECTED"
    assert "Présence humaine" in result["reason"]


def test_kyc_without_liveness_token_is_skipped() -> None:
    response = client.get("/api/kyc/stream?voice=false")
    events = _parse_sse(response.text)
    liveness = [d for t, d in events if t == "liveness_check"]
    assert liveness and liveness[0]["status"] == "SKIPPED"
    result = [d for t, d in events if t == "kyc_result"][0]
    assert result["verdict"] == "APPROVED"


def test_kyc_pdf_contains_liveness_section(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.setitem(sys.modules, "fpdf", None)
    token = _verified_token()
    response = client.get(f"/api/kyc/stream?voice=false&liveness_token={token}")
    done = [d for t, d in _parse_sse(response.text) if t == "done"][0]
    import base64

    pdf = base64.b64decode(done["pdf_b64"])
    text = pdf.decode("latin-1")
    assert "APPROVED" in text
