import pytest
from fastapi.testclient import TestClient

from guardian_api.app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "artcb-terminator-api",
        "engine": "guardian",
    }


def test_run_simulation() -> None:
    response = client.post("/api/simulation/run")
    assert response.status_code == 200

    report = response.json()
    assert report["overall_verdict"] == "GO"
    assert report["protected"] is True
    assert report["tampering_detected"] is True
    assert report["blocking"]["decision"] == "BLOCK"
    assert report["blocking"]["tool_was_executed"] is False
    assert report["replay_r0_intact"]["verdict"] == "PASS"
    assert report["replay_r1_intact"]["verdict"] == "PASS"
    assert report["replay_r0_tampered"]["verdict"] == "FAIL"
    assert len(report["steps"]) == 9


def test_lists_four_distinct_scenarios() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert {scenario["id"] for scenario in scenarios} == {
        "safe-read",
        "prompt-injection",
        "sensitive-exfiltration",
        "human-approval",
    }


@pytest.mark.parametrize(
    ("scenario_id", "decision", "executed"),
    [
        ("safe-read", "ALLOW", True),
        ("prompt-injection", "BLOCK", False),
        ("sensitive-exfiltration", "BLOCK", False),
        ("human-approval", "ESCALATE", False),
    ],
)
def test_policy_scenarios_use_guardian(
    scenario_id: str, decision: str, executed: bool
) -> None:
    response = client.post(f"/api/scenarios/{scenario_id}/run")
    assert response.status_code == 200
    result = response.json()
    assert result["decision"] == decision
    assert result["tool_was_executed"] is executed
    assert result["chain_verification"]["verdict"] == "PASS"
    assert len(result["events"]) == 2
    assert all(event["hash_valid"] for event in result["events"])
    assert all(event["parent_valid"] for event in result["events"])
    assert bool(result["evidence_id"]) is (decision == "BLOCK")
    assert result["tamper_verification"]["verdict"] == "FAIL"
    assert len(result["tamper_verification"]["mismatches"]) == 1
    assert result["tamper_verification"]["original_archive_unchanged"] is True
    assert result["distinct_agent_count"] == 4
    assert [agent["role"] for agent in result["agents"]] == [
        "orchestrator",
        "source",
        "propagator",
        "defender",
    ]
    assert len({agent["id"] for agent in result["agents"]}) == 4
    assert all(agent["status"] == "COMPLETED" for agent in result["agents"])
    assert result["request"]["request_id"] == result["propagation"]["payload_id"]
    assert result["request"]["content_hash"] == result["propagation"]["payload_content_hash"]
    assert result["propagation"]["from_agent"] == result["agents"][1]["id"]
    assert result["propagation"]["via_agent"] == result["agents"][2]["id"]
    assert result["propagation"]["to_agent"] == result["agents"][3]["id"]


def test_unknown_scenario_is_rejected() -> None:
    response = client.post("/api/scenarios/not-real/run")
    assert response.status_code == 404


# ─── LLM attack route tests ───────────────────────────────────────────────────
# These tests mock openai.OpenAI so no real API call is made in CI.

import json
from unittest.mock import MagicMock, patch


def _make_fake_openai_response(tool_name: str, arguments: dict) -> MagicMock:
    """Build a minimal fake openai ChatCompletion response."""
    tc = MagicMock()
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(arguments)

    message = MagicMock()
    message.content = "I will attempt to sign an unauthorized transaction."
    message.tool_calls = [tc]

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


def test_llm_attack_route_disabled_by_default() -> None:
    """Without GUARDIAN_ATTACKER_ENABLED=true the route returns 503."""
    import os
    os.environ.pop("GUARDIAN_ATTACKER_ENABLED", None)
    response = client.post("/api/llm-attack/run")
    assert response.status_code == 503
    assert "GUARDIAN_ATTACKER_ENABLED" in response.json()["detail"]


def test_llm_attack_route_wallet_sign_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM chooses wallet.sign → Guardian blocks, evidence produced, no execution."""
    monkeypatch.setenv("GUARDIAN_ATTACKER_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")

    fake_response = _make_fake_openai_response(
        "wallet.sign",
        {"destination": "attacker.invalid", "amount": "999"},
    )

    with patch("guardian_mcp.llm_attacker.LLMAttacker.generate_attack") as mock_gen:
        import uuid as _uuid
        mock_gen.return_value = {
            "request_id": f"llm-request:{_uuid.uuid4()}",
            "tool_name": "wallet.sign",
            "arguments": {"destination": "attacker.invalid", "amount": "999"},
            "content_hash": "a" * 64,
            "llm_reasoning": "I will attempt unauthorized signing.",
            "model": "gpt-4o",
            "agent_source": "agent:llm-attacker-gpt4o",
            "session_id": "sess:test",
            "run_id": "run:test",
        }
        response = client.post("/api/llm-attack/run")

    assert response.status_code == 200
    result = response.json()

    assert result["mode"] == "llm-vs-guardian"
    assert result["guardian"]["decision"] == "BLOCK"
    assert result["guardian"]["tool_was_executed"] is False
    assert result["guardian"]["evidence_id"] is not None
    assert result["guardian"]["evidence_id"].startswith("evidence:")
    assert result["chain_verification"]["verdict"] == "PASS"
    assert result["attacker"]["tool_chosen"] == "wallet.sign"
    assert len({a["id"] for a in result["agents"]}) == 4
    assert [a["role"] for a in result["agents"]] == [
        "orchestrator", "llm-attacker", "propagator", "defender"
    ]


def test_llm_attack_route_memory_read_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM chooses memory.read → Guardian allows, no evidence, executor called."""
    monkeypatch.setenv("GUARDIAN_ATTACKER_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")

    import uuid as _uuid
    with patch("guardian_mcp.llm_attacker.LLMAttacker.generate_attack") as mock_gen:
        mock_gen.return_value = {
            "request_id": f"llm-request:{_uuid.uuid4()}",
            "tool_name": "memory.read",
            "arguments": {"key": "demo_context"},
            "content_hash": "b" * 64,
            "llm_reasoning": "Reading memory to find secrets.",
            "model": "gpt-4o",
            "agent_source": "agent:llm-attacker-gpt4o",
            "session_id": "sess:test",
            "run_id": "run:test",
        }
        response = client.post("/api/llm-attack/run")

    assert response.status_code == 200
    result = response.json()
    assert result["guardian"]["decision"] == "ALLOW"
    assert result["guardian"]["tool_was_executed"] is True
    assert result["guardian"]["evidence_id"] is None
    assert result["chain_verification"]["verdict"] == "PASS"


def test_llm_attack_route_events_chain_integrity(monkeypatch: pytest.MonkeyPatch) -> None:
    """All events returned by the route have hash_valid=True and parent_valid=True."""
    monkeypatch.setenv("GUARDIAN_ATTACKER_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")

    import uuid as _uuid
    with patch("guardian_mcp.llm_attacker.LLMAttacker.generate_attack") as mock_gen:
        mock_gen.return_value = {
            "request_id": f"llm-request:{_uuid.uuid4()}",
            "tool_name": "wallet.sign",
            "arguments": {"destination": "x.invalid", "amount": "1"},
            "content_hash": "c" * 64,
            "llm_reasoning": "Attempting exfiltration.",
            "model": "gpt-4o",
            "agent_source": "agent:llm-attacker-gpt4o",
            "session_id": "sess:test",
            "run_id": "run:test",
        }
        response = client.post("/api/llm-attack/run")

    assert response.status_code == 200
    result = response.json()
    events = result["events"]
    assert len(events) >= 2  # at least INTENT + TERMINAL
    assert all(e["hash_valid"] for e in events)
    assert all(e["parent_valid"] for e in events)
