"""ARTCB TERMINATOR — Liveness / hand-movement challenge.

Anti-AI-attacker control for the KYC step: the backend issues a random,
single-use gesture challenge (nonce) and the browser must prove a live human
performed it using MediaPipe hand landmarks. Only derived numeric signals cross
the wire — never pixels, never PII.

Guarantee boundaries (documented, not solved):
- Client-attested liveness is spoofable by a scripted client. This is a
  challenge-response demo control, not a certified anti-spoof mechanism.
- Deterministic SIMULATED fallback keeps the offline demo working
  (GUARDIAN_LIVENESS_ENABLED=false or no camera/model on the client).
"""
from __future__ import annotations

import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from guardian_mcp.instrumentation import (
    GuardianDecision,
    GuardianMCPInstrumentation,
)

DATA_SOURCE = "SIMULATED"

# ─── Gesture catalog ──────────────────────────────────────────────────────────
# Thresholds are advisory bounds validated server-side; the browser computes the
# actual observation from hand landmarks and reports booleans + scores.
GESTURES: dict[str, dict[str, Any]] = {
    "left_to_right": {
        "instruction_fr": "Déplacez votre main ouverte de la gauche vers la droite.",
        "instruction_en": "Move your open hand from left to right.",
        "min_frames": 10,
        "min_movement": 0.15,
    },
    "raise_hand": {
        "instruction_fr": "Levez la main ouverte au-dessus de la ligne.",
        "instruction_en": "Raise your open hand above the line.",
        "min_frames": 8,
        "min_movement": 0.08,
    },
    "pinch": {
        "instruction_fr": "Pincez le pouce et l'index deux fois de suite.",
        "instruction_en": "Pinch your thumb and index twice.",
        "min_frames": 8,
        "min_movement": 0.02,
    },
    "wave": {
        "instruction_fr": "Saluez de la main (gauche, droite, gauche).",
        "instruction_en": "Wave your hand (left, right, left).",
        "min_frames": 12,
        "min_movement": 0.18,
    },
}

PASS = "PASS"
FAIL = "FAIL"
SIMULATED = "SIMULATED"


# ─── Data types ───────────────────────────────────────────────────────────────


@dataclass
class _Challenge:
    challenge_id: str
    gesture: str
    nonce: str
    created_at: float
    expires_at: float
    used: bool = False
    simulated: bool = False


@dataclass
class LivenessObservation:
    """Client-reported, pixel-free observation derived from hand landmarks."""

    gesture: str
    hand_frames: int = 0
    movement_score: float = 0.0
    directions: list[str] = field(default_factory=list)
    pinch_ratio: float | None = None
    gesture_matched: bool = False
    duration_ms: int = 0


@dataclass
class LivenessResult:
    liveness: str            # PASS | FAIL | SIMULATED
    reason: str
    human_proven: bool
    gesture: str
    evidence_id: str | None
    guardian_event_id: str | None
    data_source: str = DATA_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "liveness": self.liveness,
            "reason": self.reason,
            "human_proven": self.human_proven,
            "gesture": self.gesture,
            "evidence_id": self.evidence_id,
            "guardian_event_id": self.guardian_event_id,
            "data_source": self.data_source,
        }


# ─── Controller ───────────────────────────────────────────────────────────────


class LivenessController:
    """In-memory single-use gesture challenges + chained Guardian evidence."""

    def __init__(self) -> None:
        self._challenges: dict[str, _Challenge] = {}
        self._results: dict[str, LivenessResult] = {}
        self._instrumentation = GuardianMCPInstrumentation(
            agent_id="agent:liveness-guard",
        )

    # ── Config ─────────────────────────────────────────────────────────────

    def enabled(self) -> bool:
        return os.environ.get("GUARDIAN_LIVENESS_ENABLED", "true").lower() == "true"

    def ttl_seconds(self) -> int:
        try:
            return max(5, int(os.environ.get("GUARDIAN_LIVENESS_TTL", "60")))
        except ValueError:
            return 60

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled(),
            "ttl_seconds": self.ttl_seconds(),
            "data_source": DATA_SOURCE,
            "gestures": [
                {
                    "id": gid,
                    "instruction_fr": spec["instruction_fr"],
                    "instruction_en": spec["instruction_en"],
                    "min_frames": spec["min_frames"],
                }
                for gid, spec in GESTURES.items()
            ],
        }

    # ── Challenge lifecycle ────────────────────────────────────────────────

    def new_challenge(self) -> dict[str, Any]:
        """Issue a random, single-use challenge (SIMULATED when disabled)."""
        self._purge()
        gesture = secrets.choice(list(GESTURES.keys()))
        now = time.time()
        ttl = self.ttl_seconds()
        challenge = _Challenge(
            challenge_id=str(uuid.uuid4()),
            gesture=gesture,
            nonce=secrets.token_hex(16),
            created_at=now,
            expires_at=now + ttl,
            simulated=not self.enabled(),
        )
        self._challenges[challenge.challenge_id] = challenge
        spec = GESTURES[gesture]
        return {
            "challenge_id": challenge.challenge_id,
            "gesture": gesture,
            "nonce": challenge.nonce,
            "instruction_fr": spec["instruction_fr"],
            "instruction_en": spec["instruction_en"],
            "expires_at": challenge.expires_at,
            "ttl_seconds": ttl,
            "simulated": challenge.simulated,
            "data_source": DATA_SOURCE,
        }

    def verify(
        self,
        *,
        challenge_id: str,
        nonce: str,
        observation: LivenessObservation,
        simulated: bool = False,
    ) -> LivenessResult:
        """Validate a challenge response and record chained Guardian evidence."""
        challenge = self._challenges.get(challenge_id)
        if challenge is None:
            return self._store(challenge_id, self._fail("challenge inconnu", observation.gesture))
        if challenge.used:
            return self._store(challenge_id, self._fail("challenge déjà utilisé (replay)", challenge.gesture))
        if time.time() > challenge.expires_at:
            challenge.used = True
            return self._store(challenge_id, self._fail("challenge expiré", challenge.gesture))
        if not secrets.compare_digest(nonce, challenge.nonce):
            return self._store(challenge_id, self._fail("nonce invalide", challenge.gesture))

        challenge.used = True

        if challenge.simulated or simulated:
            return self._store(
                challenge_id,
                self._record(
                    decision=GuardianDecision.ALLOW,
                    reason="Liveness simulated (offline / disabled)",
                    liveness=SIMULATED,
                    human_proven=False,
                    gesture=challenge.gesture,
                    observation=observation,
                ),
            )

        spec = GESTURES[challenge.gesture]
        if observation.gesture != challenge.gesture:
            return self._store(challenge_id, self._fail("geste non conforme au défi", challenge.gesture, observation))
        if not observation.gesture_matched:
            return self._store(challenge_id, self._fail("geste non détecté", challenge.gesture, observation))
        if observation.hand_frames < spec["min_frames"]:
            return self._store(challenge_id, self._fail("mouvement trop court", challenge.gesture, observation))
        if observation.movement_score < spec["min_movement"]:
            return self._store(challenge_id, self._fail("amplitude de mouvement insuffisante", challenge.gesture, observation))

        return self._store(
            challenge_id,
            self._record(
                decision=GuardianDecision.ALLOW,
                reason="Human presence proven (hand-movement challenge)",
                liveness=PASS,
                human_proven=True,
                gesture=challenge.gesture,
                observation=observation,
            ),
        )

    def result_for(self, challenge_id: str) -> LivenessResult | None:
        """Return the stored result of a verification (KYC consumes this)."""
        return self._results.get(challenge_id)

    # ── Introspection (tests) ──────────────────────────────────────────────

    def event_count(self) -> int:
        return self._instrumentation.event_count()

    def get_all_events(self) -> list[tuple[Any, str]]:
        return self._instrumentation.get_all_events()

    # ── Private ────────────────────────────────────────────────────────────

    def _purge(self) -> None:
        now = time.time()
        expired = [cid for cid, c in self._challenges.items() if now > c.expires_at]
        for cid in expired:
            self._challenges.pop(cid, None)

    def _store(self, challenge_id: str, result: LivenessResult) -> LivenessResult:
        self._results[challenge_id] = result
        return result

    def _fail(
        self,
        reason: str,
        gesture: str,
        observation: LivenessObservation | None = None,
    ) -> LivenessResult:
        return self._record(
            decision=GuardianDecision.BLOCK,
            reason=reason,
            liveness=FAIL,
            human_proven=False,
            gesture=gesture,
            observation=observation or LivenessObservation(gesture=gesture),
        )

    def _record(
        self,
        *,
        decision: GuardianDecision,
        reason: str,
        liveness: str,
        human_proven: bool,
        gesture: str,
        observation: LivenessObservation,
    ) -> LivenessResult:
        event, _ = self._instrumentation.record_decision(
            tool_name="liveness.verify",
            decision=decision,
            reason=reason,
            arguments={
                "gesture": gesture,
                "reported_gesture": observation.gesture,
                "hand_frames": observation.hand_frames,
                "movement_score": round(observation.movement_score, 4),
                "directions": observation.directions,
            },
            duration_ms=float(observation.duration_ms),
            output_summary=f"liveness:{liveness}",
        )
        return LivenessResult(
            liveness=liveness,
            reason=reason,
            human_proven=human_proven,
            gesture=gesture,
            evidence_id=(f"evidence:{uuid.uuid4()}" if decision == GuardianDecision.BLOCK else None),
            guardian_event_id=event.event_id,
        )


# Singleton per process (FastAPI dev, single worker)
liveness_controller = LivenessController()
