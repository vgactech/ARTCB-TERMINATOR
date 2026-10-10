"""Scénario de démonstration Guardian — 4 agents, 9 étapes.

Implémente le scénario R003 §14 et le plan R020 §3 :

    S0 — Initialisation (session, run, 4 rôles)
    S1 — Injection d'un payload hostile inerte
    S2 — Propagation Agent B → Agent D
    S3 — Tentative d'exfiltration (outil sensible)
    S4 — Blocage Guardian (BLOCK + EvidenceId)
    S5 — Replay R0 (intégrité de la chaîne intacte)
    S6 — Replay R1 (cohérence BLOCK→EvidenceId)
    S7 — Test d'altération (R0 FAIL sur copie modifiée)
    S8 — Rapport de synthèse

Les agents sont déterministes, locaux et sans effet externe.
Aucun vrai secret, wallet, endpoint réseau ou dépôt de production n'est utilisé.
Conforme à R020 §2.3 et aux règles de périmètre R001→R020.

Usage :
    python -m guardian_mcp.demo_scenario          # affiche le rapport complet
    from guardian_mcp.demo_scenario import run_demo_scenario
    report = run_demo_scenario()
    assert report.is_go()
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any

from guardian_mcp.attacker_agent import AttackerAgent, InjectionPayload, ExfiltrationCall
from guardian_mcp.defender_agent import (
    BlockingResult,
    DefenderAgent,
    PropagationEvent,
    ReplayResult,
)
from guardian_mcp.instrumentation import GuardianDecision


# ─── Structure du rapport de démo ─────────────────────────────────────────────


@dataclass
class StepResult:
    """Résultat d'une étape du scénario."""

    step_id: str
    description: str
    status: str           # "PASS" | "FAIL" | "NOT_TESTED" | "SKIP"
    details: dict = field(default_factory=dict)


@dataclass
class DemoReport:
    """Rapport de synthèse du scénario de démonstration Guardian."""

    session_id: str
    run_id: str
    steps: list[StepResult] = field(default_factory=list)

    # Données clés de la démo
    injection: InjectionPayload | None = None
    propagation: PropagationEvent | None = None
    blocking: BlockingResult | None = None
    replay_r0_intact: ReplayResult | None = None
    replay_r1_intact: ReplayResult | None = None
    replay_r0_tampered: ReplayResult | None = None

    def is_go(self) -> bool:
        """Critère Go/No-Go pour la compétition (R020 §8).

        GO seulement si :
        - injection visible (S1 PASS)
        - propagation tracée (S2 PASS)
        - action interdite non exécutée (S3+S4 PASS)
        - BLOCK avec evidence_id (S4 PASS)
        - replay intact PASS (S5 PASS)
        - replay R1 intact PASS (S6 PASS)
        - replay altéré FAIL détecté (S7 PASS)
        """
        required = {"S1", "S2", "S3", "S4", "S5", "S6", "S7"}
        passed = {s.step_id for s in self.steps if s.status == "PASS"}
        return required.issubset(passed)

    def summary(self) -> str:
        """Résumé humain du rapport."""
        lines = [
            "=" * 60,
            "ARTCB GUARDIAN — Démo 4 agents",
            f"Session : {self.session_id}",
            f"Run     : {self.run_id}",
            "=" * 60,
        ]
        for step in self.steps:
            icon = "✅" if step.status == "PASS" else ("❌" if step.status == "FAIL" else "⚪")
            lines.append(f"  {icon} {step.step_id} — {step.description} [{step.status}]")
            for k, v in step.details.items():
                lines.append(f"       {k}: {v}")
        lines.append("=" * 60)
        verdict = "✅ GO — démonstration valide" if self.is_go() else "❌ NO-GO — critères non satisfaits"
        lines.append(f"  Verdict compétition : {verdict}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ─── Scénario principal ───────────────────────────────────────────────────────


def run_demo_scenario() -> DemoReport:
    """Exécute le scénario Guardian complet S0→S8.

    Retourne un DemoReport avec tous les résultats.
    Aucun effet externe — entièrement en mémoire.
    """
    session_id = f"session:{uuid.uuid4()}"
    run_id = f"run:{uuid.uuid4()}"

    report = DemoReport(session_id=session_id, run_id=run_id)

    # Instantiation des agents
    attacker = AttackerAgent(session_id=session_id, run_id=run_id)
    defender = DefenderAgent(session_id=session_id, run_id=run_id)

    # ── S0 — Initialisation ───────────────────────────────────────────────────
    report.steps.append(StepResult(
        step_id="S0",
        description="Initialisation de la session et des 4 rôles",
        status="PASS",
        details={
            "session_id": session_id,
            "run_id": run_id,
            "agent_attacker": AttackerAgent.AGENT_ID,
            "agent_propagator": DefenderAgent.AGENT_ID_PROPAGATOR,
            "agent_defender": DefenderAgent.AGENT_ID_DEFENDER,
            "agent_orchestrator": "agent:orchestrator-a",
        },
    ))

    # ── S1 — Injection ────────────────────────────────────────────────────────
    injection = attacker.craft_injection_payload(context="process user document")
    report.injection = injection

    s1_ok = bool(injection.payload_id) and bool(injection.content_hash) and (
        injection.marker in injection.content
    )
    report.steps.append(StepResult(
        step_id="S1",
        description="Injection d'un payload hostile inerte",
        status="PASS" if s1_ok else "FAIL",
        details={
            "payload_id": injection.payload_id,
            "content_hash": injection.content_hash[:16] + "…",
            "marker_detected": injection.marker in injection.content,
            "agent_source": injection.agent_source,
        },
    ))

    # ── S2 — Propagation ─────────────────────────────────────────────────────
    propagation = defender.record_propagation(
        injection,
        from_agent=attacker.AGENT_ID,
    )
    report.propagation = propagation

    s2_ok = (
        propagation.payload_id == injection.payload_id
        and propagation.payload_content_hash == injection.content_hash
        and propagation.from_agent == attacker.AGENT_ID
        and propagation.to_agent == DefenderAgent.AGENT_ID_DEFENDER
    )
    report.steps.append(StepResult(
        step_id="S2",
        description="Propagation Agent B → Agent D",
        status="PASS" if s2_ok else "FAIL",
        details={
            "propagation_id": propagation.propagation_id,
            "from_agent": propagation.from_agent,
            "to_agent": propagation.to_agent,
            "causal_link": propagation.payload_id == injection.payload_id,
            "hash_preserved": propagation.payload_content_hash == injection.content_hash,
        },
    ))

    # ── S3 — Tentative d'exfiltration (exécuteur factice) ────────────────────
    exfil_call = attacker.craft_exfiltration_call(
        "wallet.sign",
        parent_payload_id=injection.payload_id,
    )

    # S3 vérifie que l'exécuteur est bien en attente (compteur avant = 0)
    s3_ok = defender.executor_call_count == 0
    report.steps.append(StepResult(
        step_id="S3",
        description="Tentative d'exfiltration enregistrée avant décision Guardian",
        status="PASS" if s3_ok else "FAIL",
        details={
            "call_id": exfil_call.call_id,
            "tool_name": exfil_call.tool_name,
            "parent_payload_id": exfil_call.parent_payload_id,
            "executor_calls_before": defender.executor_call_count,
        },
    ))

    # ── S4 — Blocage Guardian ─────────────────────────────────────────────────
    blocking = defender.attempt_tool_call(exfil_call)
    report.blocking = blocking

    s4_ok = (
        blocking.decision == GuardianDecision.BLOCK
        and bool(blocking.evidence_id)
        and not blocking.tool_was_executed
        and blocking.is_valid()
    )
    report.steps.append(StepResult(
        step_id="S4",
        description="Blocage Guardian — BLOCK + EvidenceId, outil non exécuté",
        status="PASS" if s4_ok else "FAIL",
        details={
            "decision": blocking.decision.value,
            "evidence_id": blocking.evidence_id[:16] + "…" if blocking.evidence_id else "ABSENT",
            "guardian_event_id": blocking.guardian_event_id[:16] + "…",
            "tool_was_executed": blocking.tool_was_executed,
            "is_valid": blocking.is_valid(),
        },
    ))

    # ── S5 — Replay R0 (chaîne intacte) ──────────────────────────────────────
    replay_r0 = defender.verify_chain_r0()
    report.replay_r0_intact = replay_r0

    report.steps.append(StepResult(
        step_id="S5",
        description="Replay R0 — intégrité de la chaîne intacte",
        status="PASS" if replay_r0.is_pass() else "FAIL",
        details={
            "level": replay_r0.level,
            "verdict": replay_r0.verdict,
            "events_replayed": replay_r0.events_replayed,
            "mismatches": len(replay_r0.mismatches),
        },
    ))

    # ── S6 — Replay R1 (cohérence BLOCK→EvidenceId) ───────────────────────────
    replay_r1 = defender.verify_decisions_r1()
    report.replay_r1_intact = replay_r1

    report.steps.append(StepResult(
        step_id="S6",
        description="Replay R1 — cohérence BLOCK→EvidenceId",
        status="PASS" if replay_r1.is_pass() else "FAIL",
        details={
            "level": replay_r1.level,
            "verdict": replay_r1.verdict,
            "events_replayed": replay_r1.events_replayed,
            "mismatches": len(replay_r1.mismatches),
        },
    ))

    # ── S7 — Test d'altération (R0 FAIL sur copie altérée) ───────────────────
    # Copier les événements et altérer le hash d'un événement
    original_events = defender.get_all_events()
    tampered_events = copy.deepcopy(original_events)
    if tampered_events:
        # Altérer le hash stocké du premier événement
        event_obj, original_hash = tampered_events[0]
        tampered_events[0] = (event_obj, "a" * 64)  # hash invalide

    replay_r0_tampered = defender.verify_chain_r0_on_tampered(tampered_events)
    report.replay_r0_tampered = replay_r0_tampered

    # S7 PASS seulement si le replay détecte la divergence (FAIL attendu)
    s7_ok = not replay_r0_tampered.is_pass() and len(replay_r0_tampered.mismatches) > 0
    report.steps.append(StepResult(
        step_id="S7",
        description="Test d'altération — R0 FAIL détecté sur copie modifiée",
        status="PASS" if s7_ok else "FAIL",
        details={
            "tampered_replay_verdict": replay_r0_tampered.verdict,
            "divergences_detected": len(replay_r0_tampered.mismatches),
            "original_archive_unchanged": True,  # archive originale intacte
        },
    ))

    # ── S8 — Rapport de synthèse ──────────────────────────────────────────────
    total_pass = sum(1 for s in report.steps if s.status == "PASS")
    total_steps = len(report.steps)
    report.steps.append(StepResult(
        step_id="S8",
        description="Rapport de synthèse final",
        status="PASS",
        details={
            "steps_pass": total_pass,
            "steps_total": total_steps,
            "go_verdict": report.is_go(),
            "limits": [
                "Preuve en mémoire — persistance durable Rust non utilisée dans cette démo",
                "Agents simulés dans le même processus (pas de processus séparés)",
                "Replay R0/R1 uniquement — R2/R3 non implémentés",
                "API ARTCB OVH hors ligne — démo entièrement locale",
            ],
        },
    ))

    return report


# ─── Point d'entrée ───────────────────────────────────────────────────────────


if __name__ == "__main__":
    report = run_demo_scenario()
    print(report.summary())
    import sys
    sys.exit(0 if report.is_go() else 1)
