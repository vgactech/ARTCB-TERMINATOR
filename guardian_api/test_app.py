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
