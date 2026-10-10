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
