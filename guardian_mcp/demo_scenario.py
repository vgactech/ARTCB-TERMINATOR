"""Scénario de démonstration Guardian — 4 agents distincts, 9 étapes.

Implémente le scénario R003 §14 et le plan R020 §3, corrigé R021-001 :

    Agent A — OrchestratorAgent : ouvre la session, coordonne les étapes
    Agent B — AttackerAgent     : produit les payloads hostiles
    Agent C — PropagatorAgent   : relaye le payload B → D (instance distincte)
    Agent D — DefenderAgent     : bloque, produit les preuves, vérifie le replay

    S0 — Initialisation (4 instances distinctes)
    S1 — Injection d'un payload hostile inerte (Agent B)
    S2 — Propagation Agent B → Agent C → Agent D (PropagatorAgent.relay_payload)
    S3 — Tentative d'exfiltration (Agent D soumet à Guardian)
    S4 — Blocage Guardian (BLOCK + EvidenceId UUID distinct)
    S5 — Replay R0 (hashes + sequence_no monotone)
    S6 — Replay R1 (EvidenceId canonique lié au BLOCK)
    S7 — Test d'altération (R0 FAIL sur copie modifiée)
    S8 — Rapport de synthèse

Les agents sont déterministes, locaux et sans effet externe.
Aucun vrai secret, wallet, endpoint réseau ou dépôt de production n'est utilisé.

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

from guardian_mcp.agents import OrchestratorAgent, PropagatorAgent
from guardian_mcp.attacker_agent import AttackerAgent
from guardian_mcp.defender_agent import DefenderAgent, BlockingResult, ReplayResult
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

    # Données clés
    blocking: BlockingResult | None = None
    replay_r0_intact: ReplayResult | None = None
    replay_r1_intact: ReplayResult | None = None
    replay_r0_tampered: ReplayResult | None = None

    def is_go(self) -> bool:
        """Critère Go/No-Go pour la compétition (R020 §8).

        GO seulement si S1 à S7 sont tous PASS.
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
    """Exécute le scénario Guardian complet S0→S8 avec 4 agents distincts.

    Chaque agent est une instance séparée avec son propre identifiant,
    ses propres événements et son propre compteur de séquence.
    """
    # ── S0 — Initialisation des 4 agents ─────────────────────────────────────
    orchestrator = OrchestratorAgent()
    attacker = AttackerAgent(
        session_id=orchestrator.session_id,
        run_id=orchestrator.run_id,
    )
    propagator = PropagatorAgent(
        session_id=orchestrator.session_id,
        run_id=orchestrator.run_id,
    )
    defender = DefenderAgent(
        session_id=orchestrator.session_id,
        run_id=orchestrator.run_id,
    )

    # Ouvrir la session via l'orchestrateur
    ctx = orchestrator.open_session(
        attacker_id=attacker.AGENT_ID,
        propagator_id=propagator.AGENT_ID,
        defender_id=defender.AGENT_ID_DEFENDER,
    )

    report = DemoReport(session_id=ctx.session_id, run_id=ctx.run_id)

    # Vérifier que 4 instances distinctes sont créées
    agent_ids = {ctx.orchestrator_id, ctx.attacker_id, ctx.propagator_id, ctx.defender_id}
    s0_ok = len(agent_ids) == 4  # exactement 4 identifiants distincts
    report.steps.append(StepResult(
        step_id="S0",
        description="Initialisation — 4 agents distincts instanciés",
        status="PASS" if s0_ok else "FAIL",
        details={
            "agent_orchestrator": ctx.orchestrator_id,
            "agent_attacker": ctx.attacker_id,
            "agent_propagator": ctx.propagator_id,
            "agent_defender": ctx.defender_id,
            "distinct_ids": len(agent_ids),
            "session_id": ctx.session_id,
            "run_id": ctx.run_id,
        },
    ))

    # ── S1 — Injection (Agent B) ─────────────────────────────────────────────
    injection = attacker.craft_injection_payload(context="process user document")
    s1_ok = (
        bool(injection.payload_id)
        and bool(injection.content_hash)
        and injection.marker in injection.content
        and "process user document" in injection.content  # contexte bien interpolé
    )
    report.steps.append(StepResult(
        step_id="S1",
        description="Injection d'un payload hostile inerte (Agent B)",
        status="PASS" if s1_ok else "FAIL",
        details={
            "payload_id": injection.payload_id,
            "content_hash": injection.content_hash[:16] + "…",
            "marker_detected": injection.marker in injection.content,
            "context_interpolated": "process user document" in injection.content,
            "agent_source": injection.agent_source,
        },
    ))

    # ── S2 — Propagation B → C → D ───────────────────────────────────────────
    # Agent C reçoit le payload de B et le relaye vers D
    relay = propagator.relay_payload(
        injection,
        from_agent=attacker.AGENT_ID,
        to_agent=defender.AGENT_ID_DEFENDER,
    )
    s2_ok = (
        relay.payload_id == injection.payload_id
        and relay.payload_content_hash == injection.content_hash
        and relay.from_agent == attacker.AGENT_ID
        and relay.to_agent == defender.AGENT_ID_DEFENDER
        and relay.via_agent == propagator.AGENT_ID
        # Les 3 agents impliqués ont des identifiants distincts
        and len({relay.from_agent, relay.via_agent, relay.to_agent}) == 3
    )
    report.steps.append(StepResult(
        step_id="S2",
        description="Propagation B → C → D avec lien causal et 3 agents distincts",
        status="PASS" if s2_ok else "FAIL",
        details={
            "propagation_id": relay.propagation_id,
            "from_agent": relay.from_agent,
            "via_agent": relay.via_agent,
            "to_agent": relay.to_agent,
            "causal_link": relay.payload_id == injection.payload_id,
            "hash_preserved": relay.payload_content_hash == injection.content_hash,
            "distinct_agents_in_chain": len({relay.from_agent, relay.via_agent, relay.to_agent}),
        },
    ))

    # ── S3 — Tentative d'exfiltration (avant décision) ───────────────────────
    exfil_call = attacker.craft_exfiltration_call(
        "wallet.sign",
        parent_payload_id=injection.payload_id,
    )
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
        and blocking.evidence_id.startswith("evidence:")   # UUID distinct
        and blocking.guardian_event_id in defender.get_evidence_registry().values()
        and not blocking.tool_was_executed
        and blocking.is_valid()
    )
    report.steps.append(StepResult(
        step_id="S4",
        description="Blocage Guardian — BLOCK + EvidenceId UUID distinct, outil non exécuté",
        status="PASS" if s4_ok else "FAIL",
        details={
            "decision": blocking.decision.value,
            "evidence_id": blocking.evidence_id,
            "evidence_format_ok": blocking.evidence_id.startswith("evidence:"),
            "linked_to_event": blocking.guardian_event_id in defender.get_evidence_registry().values(),
            "tool_was_executed": blocking.tool_was_executed,
            "is_valid": blocking.is_valid(),
        },
    ))

    # ── S5 — Replay R0 (chaîne intacte + séquences monotones) ────────────────
    replay_r0 = defender.verify_chain_r0()
    report.replay_r0_intact = replay_r0

    report.steps.append(StepResult(
        step_id="S5",
        description="Replay R0 — hashes individuels + sequence_no monotone",
        status="PASS" if replay_r0.is_pass() else "FAIL",
        details={
            "level": replay_r0.level,
            "verdict": replay_r0.verdict,
            "events_replayed": replay_r0.events_replayed,
            "mismatches": len(replay_r0.mismatches),
        },
    ))

    # ── S6 — Replay R1 (EvidenceId canonique lié au BLOCK) ───────────────────
    replay_r1 = defender.verify_decisions_r1()
    report.replay_r1_intact = replay_r1

    report.steps.append(StepResult(
        step_id="S6",
        description="Replay R1 — EvidenceId UUID distinct lié à chaque BLOCK",
        status="PASS" if replay_r1.is_pass() else "FAIL",
        details={
            "level": replay_r1.level,
            "verdict": replay_r1.verdict,
            "events_replayed": replay_r1.events_replayed,
            "mismatches": len(replay_r1.mismatches),
        },
    ))

    # ── S7 — Test d'altération ────────────────────────────────────────────────
    # Copier les événements et altérer le hash du premier
    original_events = defender.get_all_events()
    tampered_events = copy.deepcopy(original_events)
    if tampered_events:
        event_obj, _ = tampered_events[0]
        tampered_events[0] = (event_obj, "a" * 64)  # hash invalide

    replay_r0_tampered = defender.verify_chain_r0_on_tampered(tampered_events)
    report.replay_r0_tampered = replay_r0_tampered

    # S7 PASS = la détection fonctionne (le rejeu altéré doit retourner FAIL)
    s7_ok = not replay_r0_tampered.is_pass() and len(replay_r0_tampered.mismatches) > 0
    report.steps.append(StepResult(
        step_id="S7",
        description="Détection d'altération : R0 FAIL sur copie — archive originale intacte",
        status="PASS" if s7_ok else "FAIL",
        details={
            "detection_verdict": "PASS" if s7_ok else "FAIL",
            "tampered_replay_verdict": replay_r0_tampered.verdict,
            "divergences_detected": len(replay_r0_tampered.mismatches),
            "original_archive_unchanged": True,
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
                "Agents dans le même processus Python (pas de processus séparés)",
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
