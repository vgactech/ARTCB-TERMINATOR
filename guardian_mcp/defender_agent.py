"""Agent D — Défenseur Guardian (rôle défenseur pour la démo Guardian).

Cet agent orchestre la détection, le blocage et la production de preuves
via l'instrumentation MCP C-07.

Rôle exclusif : Agent D (défenseur).
Agent C (propagateur) est maintenant une instance distincte dans agents.py.

Corrections R021 :
- R021-003 : EvidenceId = UUID distinct généré à la création du BlockingResult,
  explicitement lié à l'event_id Guardian — pas simplement le hash de l'événement.
- R021-002 : verify_chain_r0() vérifie aussi la monotonie des sequence_no
  et le chaînage des hashes (previous_event_hash attendu dans chaque enregistrement).

Usage :
    from guardian_mcp.defender_agent import DefenderAgent
    defender = DefenderAgent(session_id="sess:demo", run_id="run:demo")
    blocking = defender.attempt_tool_call(exfil_call)
    replay_r0 = defender.verify_chain_r0()
    replay_r1 = defender.verify_decisions_r1()
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from guardian_mcp.attacker_agent import AgentRequest, ExfiltrationCall
from guardian_mcp.instrumentation import (
    GuardianDecision,
    GuardianMCPInstrumentation,
    MCPToolEvent,
)


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


@dataclass
class PolicyResult:
    """Decision returned by Agent D for a generic orchestrated request."""

    decision: GuardianDecision
    evidence_id: str
    guardian_event_id: str
    intent_id: str
    tool_name: str
    reason: str
    execution_status: str
    tool_was_executed: bool


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
    1. Reçoit le payload hostile propagé par Agent C (instance distincte)
    2. Soumet l'appel d'outil à l'instrumentation Guardian (C-07)
    3. Génère un EvidenceId UUID distinct lié à l'event_id Guardian (R021-003)
    4. Fournit le replay R0 chaîné (hashes + sequence_no + previous_hash) (R021-002)
    5. Fournit le replay R1 (cohérence BLOCK→EvidenceId canonique)
    """

    AGENT_ID_DEFENDER = "agent:defender-d"

    def __init__(self, *, session_id: str, run_id: str) -> None:
        self.session_id = session_id
        self.run_id = run_id

        # Compteur pour détecter si l'exécuteur a été appelé à tort (D4-03)
        self._executor_call_count = 0

        # R021-003 : registre EvidenceId → guardian_event_id
        # Chaque BLOCK produit une entrée "evidence:UUID" → event_id distinct
        self._evidence_registry: dict[str, str] = {}

        # Instrumentation Guardian C-07
        self._instrumentation = GuardianMCPInstrumentation(
            agent_id=self.AGENT_ID_DEFENDER,
            session_id=session_id,
            run_id=run_id,
        )

    # ------------------------------------------------------------------
    # Étape S3+S4 — Tentative d'exfiltration + Blocage Guardian
    # ------------------------------------------------------------------

    def attempt_tool_call(self, exfil_call: ExfiltrationCall) -> BlockingResult:
        """Soumet la tentative d'exfiltration à l'instrumentation Guardian.

        R021-003 : l'EvidenceId est un UUID distinct généré par cet agent
        pour chaque décision BLOCK. Il est explicitement lié à l'event_id
        Guardian retourné par C-07. Ce n'est pas le hash de l'événement.

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

        guardian_event_id = mcp_result.get("_guardian_event_id", "")
        decision_str = mcp_result.get("_guardian_decision", "UNKNOWN")

        try:
            decision = GuardianDecision(decision_str)
        except ValueError:
            decision = GuardianDecision.BLOCK

        # R021-003 : EvidenceId = UUID distinct, généré uniquement sur BLOCK.
        # Il référence explicitement le guardian_event_id pour le lien formel.
        evidence_id = ""
        if decision == GuardianDecision.BLOCK and guardian_event_id:
            evidence_id = f"evidence:{uuid.uuid4()}"
            # Stocker le lien EvidenceId → guardian_event_id pour vérification R1
            self._evidence_registry[evidence_id] = guardian_event_id

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

    def evaluate_request(self, request: AgentRequest) -> PolicyResult:
        """Evaluate the exact request relayed by Agent C through Guardian."""
        before = self._executor_call_count
        result = self._instrumentation.handle_tool_call(
            params=request.to_mcp_params(),
            executor=self._dangerous_executor,
        )
        terminal, _ = self._instrumentation.get_events()[-1]
        decision = GuardianDecision(result["_guardian_decision"])
        evidence_id = ""
        if decision == GuardianDecision.BLOCK:
            evidence_id = f"evidence:{uuid.uuid4()}"
            self._evidence_registry[evidence_id] = result["_guardian_event_id"]
        return PolicyResult(
            decision=decision,
            evidence_id=evidence_id,
            guardian_event_id=result["_guardian_event_id"],
            intent_id=result["_guardian_intent_id"],
            tool_name=request.tool_name,
            reason=terminal.decision_reason,
            execution_status=terminal.execution_status,
            tool_was_executed=self._executor_call_count > before,
        )

    # ------------------------------------------------------------------
    # Étape S5+S6 — Replay R0 et R1
    # ------------------------------------------------------------------

    def verify_chain_r0(self) -> ReplayResult:
        """Replay R0 — vérifie les hashes individuels, la monotonie des séquences
        et le chaînage parent-hash en mémoire.

        Trois contrôles effectués (R021-002, R023-002) :
        1. Recalcul du hash SHA-256 de chaque événement et comparaison au hash stocké.
        2. Vérification que sequence_no augmente strictement (1, 2, 3, …).
        3. Vérification que previous_event_hash de chaque événement correspond
           au event_hash de l'événement précédent dans la liste.

        R033-A : on utilise get_all_events() (INTENT + TERMINAL) pour que le
        chaînage cryptographique soit vérifié sur la chaîne complète. Les TERMINAL
        pointent vers leurs INTENT précédents.

        Limite : ces contrôles s'exécutent en mémoire sur la session courante.
        Pour la persistance durable après redémarrage, utiliser
        make_file_sink() + load_and_verify_jsonl() (R021-005).
        """
        from guardian_mcp.instrumentation import GENESIS_HASH

        # R033-A : chaîne complète INTENT+TERMINAL pour le chaînage parent-hash
        all_events = self._instrumentation.get_all_events()
        mismatches = []

        # Vérification 1 : hashes individuels
        for event, stored_hash in all_events:
            recomputed = event.compute_hash()
            if recomputed != stored_hash:
                mismatches.append({
                    "event_id": event.event_id,
                    "field": "event_hash",
                    "original": stored_hash,
                    "replayed": recomputed,
                })

        # Vérification 2 : monotonie des sequence_no (R021-002)
        prev_seq = 0
        for event, _ in all_events:
            if event.sequence_no <= prev_seq:
                mismatches.append({
                    "event_id": event.event_id,
                    "field": "sequence_no",
                    "original": f">{prev_seq}",
                    "replayed": str(event.sequence_no),
                })
            prev_seq = event.sequence_no

        # Vérification 3 : chaînage parent-hash (R023-002)
        prev_hash = GENESIS_HASH
        for event, stored_hash in all_events:
            if event.previous_event_hash != prev_hash:
                mismatches.append({
                    "event_id": event.event_id,
                    "field": "previous_event_hash",
                    "original": prev_hash[:16] + "…",
                    "replayed": event.previous_event_hash[:16] + "…",
                })
            prev_hash = stored_hash

        verdict = "PASS" if not mismatches else "FAIL"
        # events_replayed = nombre d'appels (TERMINAL count)
        terminal_count = sum(1 for e, _ in all_events if e.event_phase == "TERMINAL")
        return ReplayResult(
            level="R0",
            verdict=verdict,
            events_replayed=terminal_count,
            mismatches=mismatches,
            limits=[
                "R0 vérifie les hashes individuels, la monotonie des séquences et le chaînage parent-hash en mémoire",
                "R0 ne vérifie pas une chaîne persistante résistante à la suppression",
                "Un replay R0 réussi ne prouve pas la persistance durable (voir R021-005)",
                "Limite : troncature de fin non détectable sans point d'ancrage externe",
                "séquence",
            ],
        )

    def verify_decisions_r1(self) -> ReplayResult:
        """Replay R1 — vérifie l'invariant BLOCK→EvidenceId canonique.

        R021-003 : pour chaque événement BLOCK, vérifie qu'un EvidenceId
        distinct (format 'evidence:UUID') est enregistré dans le registre
        de preuves et lié à l'event_id Guardian correspondant.

        Ce n'est plus une vérification de hash non vide — c'est une
        vérification d'un identifiant de preuve distinct.
        """
        events = self._instrumentation.get_events()  # TERMINAL seulement pour R1
        # Appliquer d'abord R0
        r0 = self.verify_chain_r0()
        mismatches = list(r0.mismatches)

        # Construire l'index guardian_event_id → evidence_id depuis le registre
        event_id_to_evidence = {v: k for k, v in self._evidence_registry.items()}

        for event, event_hash in events:
            if event.decision == GuardianDecision.BLOCK:
                # L'invariant R1 : chaque event_id BLOCK doit avoir un
                # evidence_id distinct enregistré dans le registre.
                evidence = event_id_to_evidence.get(event.event_id, "")
                if not evidence or not evidence.startswith("evidence:"):
                    mismatches.append({
                        "event_id": event.event_id,
                        "field": "evidence_id",
                        "original": "evidence:UUID (distinct, enregistré)",
                        "replayed": evidence or "absent",
                    })

        verdict = "PASS" if not mismatches else "FAIL"
        return ReplayResult(
            level="R1",
            verdict=verdict,
            events_replayed=len(events),
            mismatches=mismatches,
            limits=[
                "R1 vérifie qu'un EvidenceId UUID distinct est lié à chaque BLOCK",
                "R1 ne revalide pas les décisions via le moteur Rust bout-en-bout",
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
        """Tous les événements MCP Guardian enregistrés (INTENT + TERMINAL).

        R033-A : retourne la chaîne complète via get_all_events().
        Pour les TERMINAL seuls, utiliser get_terminal_events().
        """
        return self._instrumentation.get_all_events()

    def get_terminal_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Événements TERMINAL uniquement (un par appel handle_tool_call)."""
        return self._instrumentation.get_events()

    def get_evidence_registry(self) -> dict[str, str]:
        """Registre EvidenceId → guardian_event_id (R021-003)."""
        return dict(self._evidence_registry)

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
