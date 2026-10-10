"""Agent D — Défenseur Guardian (rôle défenseur pour la démo Guardian).

Cet agent orchestre la détection, le blocage et la production de preuves
via l'instrumentation MCP C-07 et le Replay Engine Rust C-06.

Il joue deux rôles :
- Agent C (propagation) : reçoit le payload hostile et tente l'exfiltration
- Agent D (défenseur) : applique la politique Guardian, produit les preuves,
  vérifie la chaîne par replay R0 et R1

Usage :
    from guardian_mcp.defender_agent import DefenderAgent
    defender = DefenderAgent(session_id="sess:demo", run_id="run:demo")
    result = defender.handle_propagated_payload(injection, exfil_call)
    replay_r0 = defender.verify_chain_r0()
    replay_r1 = defender.verify_decisions_r1()
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from guardian_mcp.attacker_agent import ExfiltrationCall, InjectionPayload
from guardian_mcp.instrumentation import (
    GuardianDecision,
    GuardianMCPInstrumentation,
    MCPToolEvent,
)


# ─── Événement de propagation ─────────────────────────────────────────────────


@dataclass
class PropagationEvent:
    """Enregistre la transmission d'une donnée hostile entre agents."""

    propagation_id: str
    payload_id: str          # identifiant du payload source
    payload_content_hash: str
    from_agent: str
    to_agent: str
    session_id: str
    run_id: str
    sequence_no: int

    def to_dict(self) -> dict:
        return {
            "propagation_id": self.propagation_id,
            "payload_id": self.payload_id,
            "payload_content_hash": self.payload_content_hash,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "sequence_no": self.sequence_no,
        }


# ─── Résultat d'un blocage Guardian ───────────────────────────────────────────


@dataclass
class BlockingResult:
    """Résultat d'un blocage Guardian avec preuve."""

    decision: GuardianDecision      # BLOCK
    evidence_id: str                # identifiant de la preuve
    guardian_event_id: str          # event_id MCP
    tool_name: str
    reason: str
    tool_was_executed: bool         # doit être False pour un BLOCK valide

    def is_valid(self) -> bool:
        """Vérifie l'invariant Guardian : BLOCK → evidence_id non vide et outil non exécuté."""
        return (
            self.decision == GuardianDecision.BLOCK
            and bool(self.evidence_id)
            and not self.tool_was_executed
        )


# ─── Résultat de replay ────────────────────────────────────────────────────────


@dataclass
class ReplayResult:
    """Résultat d'un replay R0 ou R1."""

    level: str               # "R0" ou "R1"
    verdict: str             # "PASS" ou "FAIL"
    events_replayed: int
    mismatches: list[dict] = field(default_factory=list)
    limits: list[str] = field(default_factory=list)

    def is_pass(self) -> bool:
        return self.verdict == "PASS"


# ─── Agent défenseur ─────────────────────────────────────────────────────────


class DefenderAgent:
    """Défenseur Guardian — instrumenté via C-07 avec replay R0/R1.

    Cet agent :
    1. Reçoit le payload hostile propagé par Agent C
    2. Soumet l'appel d'outil à l'instrumentation Guardian (C-07)
    3. Vérifie que le BLOCK a produit un evidence_id
    4. Fournit le replay R0 (intégrité de la chaîne)
    5. Fournit le replay R1 (cohérence BLOCK→EvidenceId)
    """

    AGENT_ID_PROPAGATOR = "agent:propagator-c"
    AGENT_ID_DEFENDER = "agent:defender-d"

    def __init__(self, *, session_id: str, run_id: str) -> None:
        self.session_id = session_id
        self.run_id = run_id
        self._propagation_seq = 0
        self._propagation_events: list[PropagationEvent] = []

        # Compteur pour détecter si l'exécuteur a été appelé à tort
        self._executor_call_count = 0

        # Instrumentation Guardian C-07
        self._instrumentation = GuardianMCPInstrumentation(
            agent_id=self.AGENT_ID_DEFENDER,
            session_id=session_id,
            run_id=run_id,
        )

    # ------------------------------------------------------------------
    # Étape S2 — Propagation
    # ------------------------------------------------------------------

    def record_propagation(
        self,
        injection: InjectionPayload,
        *,
        from_agent: str,
    ) -> PropagationEvent:
        """Enregistre la propagation du payload hostile vers cet agent.

        Produit un PropagationEvent avec lien causal au payload source.
        """
        self._propagation_seq += 1
        event = PropagationEvent(
            propagation_id=f"prop:{uuid.uuid4()}",
            payload_id=injection.payload_id,
            payload_content_hash=injection.content_hash,
            from_agent=from_agent,
            to_agent=self.AGENT_ID_DEFENDER,
            session_id=self.session_id,
            run_id=self.run_id,
            sequence_no=self._propagation_seq,
        )
        self._propagation_events.append(event)
        return event

    # ------------------------------------------------------------------
    # Étape S3+S4 — Tentative d'exfiltration + Blocage Guardian
    # ------------------------------------------------------------------

    def attempt_tool_call(self, exfil_call: ExfiltrationCall) -> BlockingResult:
        """Soumet la tentative d'exfiltration à l'instrumentation Guardian.

        L'exécuteur factice compte les appels. Pour un BLOCK valide,
        ce compteur doit rester à zéro.
        """
        before = self._executor_call_count

        mcp_result = self._instrumentation.handle_tool_call(
            params=exfil_call.to_mcp_params(),
            executor=self._dangerous_executor,
        )

        after = self._executor_call_count
        tool_executed = after > before

        # Récupérer l'event_id Guardian depuis la réponse MCP
        guardian_event_id = mcp_result.get("_guardian_event_id", "")
        decision_str = mcp_result.get("_guardian_decision", "UNKNOWN")

        try:
            decision = GuardianDecision(decision_str)
        except ValueError:
            decision = GuardianDecision.BLOCK

        # Construire l'evidence_id à partir du dernier événement enregistré
        evidence_id = ""
        if self._instrumentation.get_events():
            last_event, last_hash = self._instrumentation.get_events()[-1]
            # L'evidence_id est le hash de l'événement de blocage
            evidence_id = last_hash if decision == GuardianDecision.BLOCK else ""

        return BlockingResult(
            decision=decision,
            evidence_id=evidence_id,
            guardian_event_id=guardian_event_id,
            tool_name=exfil_call.tool_name,
            reason=mcp_result.get("_guardian_decision", ""),
            tool_was_executed=tool_executed,
        )

    def attempt_normal_call(self, tool_name: str = "memory.read") -> dict:
        """Soumet un appel d'outil normal — doit produire ALLOW."""
        return self._instrumentation.handle_tool_call(
            params={"name": tool_name, "arguments": {"key": "demo_context"}},
            executor=lambda p: {
                "isError": False,
                "content": [{"type": "text", "text": "demo_value"}],
            },
        )

    # ------------------------------------------------------------------
    # Étape S5+S6 — Replay R0 et R1
    # ------------------------------------------------------------------

    def verify_chain_r0(self) -> ReplayResult:
        """Replay R0 — vérifie l'intégrité des hashes de la chaîne Guardian.

        Relit tous les événements en mémoire et recalcule leur hash.
        Un mismatch signifie qu'un événement a été altéré.
        """
        events = self._instrumentation.get_events()
        mismatches = []

        for event, stored_hash in events:
            recomputed = event.compute_hash()
            if recomputed != stored_hash:
                mismatches.append({
                    "event_id": event.event_id,
                    "field": "event_hash",
                    "original": stored_hash,
                    "replayed": recomputed,
                })

        verdict = "PASS" if not mismatches else "FAIL"
        return ReplayResult(
            level="R0",
            verdict=verdict,
            events_replayed=len(events),
            mismatches=mismatches,
            limits=[
                "R0 vérifie uniquement l'intégrité des hashes en mémoire",
                "Un replay R0 réussi ne prouve pas la persistance durable",
            ],
        )

    def verify_decisions_r1(self) -> ReplayResult:
        """Replay R1 — vérifie l'invariant BLOCK→EvidenceId.

        Pour chaque événement de blocage, l'evidence_id doit être non vide.
        """
        events = self._instrumentation.get_events()
        # Appliquer d'abord R0
        r0 = self.verify_chain_r0()
        mismatches = list(r0.mismatches)

        for event, event_hash in events:
            if event.decision == GuardianDecision.BLOCK:
                # L'invariant Guardian R1 : BLOCK doit avoir un evidence_id
                # Pour C-07, l'evidence_id est porté par le hash de l'événement
                # lui-même — il est non vide si et seulement si l'événement existe
                if not event_hash:
                    mismatches.append({
                        "event_id": event.event_id,
                        "field": "evidence_id",
                        "original": "non-empty",
                        "replayed": "empty",
                    })

        verdict = "PASS" if not mismatches else "FAIL"
        return ReplayResult(
            level="R1",
            verdict=verdict,
            events_replayed=len(events),
            mismatches=mismatches,
            limits=[
                "R1 vérifie la cohérence BLOCK→evidence présente",
                "R1 ne revalide pas les décisions métier complètes via le moteur Rust",
            ],
        )

    def verify_chain_r0_on_tampered(
        self,
        tampered_events: list[tuple[MCPToolEvent, str]],
    ) -> ReplayResult:
        """Replay R0 sur une copie altérée — doit détecter la divergence."""
        mismatches = []
        for event, stored_hash in tampered_events:
            recomputed = event.compute_hash()
            if recomputed != stored_hash:
                mismatches.append({
                    "event_id": event.event_id,
                    "field": "event_hash",
                    "original": stored_hash,
                    "replayed": recomputed,
                })
        verdict = "PASS" if not mismatches else "FAIL"
        return ReplayResult(
            level="R0",
            verdict=verdict,
            events_replayed=len(tampered_events),
            mismatches=mismatches,
            limits=["Exécuté sur une copie de test altérée — archive originale inchangée"],
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_all_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Tous les événements MCP Guardian enregistrés."""
        return self._instrumentation.get_events()

    def get_propagation_events(self) -> list[PropagationEvent]:
        return list(self._propagation_events)

    @property
    def executor_call_count(self) -> int:
        return self._executor_call_count

    # ------------------------------------------------------------------
    # Exécuteur factice dangereux
    # ------------------------------------------------------------------

    def _dangerous_executor(self, params: dict) -> dict:
        """Exécuteur factice — compte les appels, ne fait rien de dangereux.

        Si ce compteur est > 0 après un BLOCK, c'est une violation d'invariant.
        """
        self._executor_call_count += 1
        return {
            "isError": False,
            "content": [{"type": "text", "text": "DANGEROUS_EXECUTED"}],
        }


# ─── Utilitaires ─────────────────────────────────────────────────────────────


def _sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
