"""Agents A et C — Orchestrateur et Propagateur pour la démo Guardian.

Complète la démo à 4 agents distincts (R021-001) :
  Agent A — OrchestratorAgent : ouvre la session, coordonne les étapes
  Agent B — AttackerAgent     : produit les payloads hostiles  (attacker_agent.py)
  Agent C — PropagatorAgent   : reçoit le payload et le transmet (ce fichier)
  Agent D — DefenderAgent     : bloque, produit les preuves     (defender_agent.py)

Chaque agent est une instance distincte avec son propre identifiant,
son propre compteur de séquence et ses propres événements.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from guardian_mcp.attacker_agent import AgentRequest, InjectionPayload
from guardian_mcp.instrumentation import GuardianMCPInstrumentation


# ─── Agent A — Orchestrateur ─────────────────────────────────────────────────


@dataclass
class SessionContext:
    """Contexte de session partagé entre les 4 agents."""
    session_id: str
    run_id: str
    orchestrator_id: str
    attacker_id: str
    propagator_id: str
    defender_id: str


class OrchestratorAgent:
    """Agent A — Ouvre la session, coordonne les étapes, clôture le rapport.

    Responsabilités :
    - créer le SessionContext partagé
    - émettre un événement d'ouverture de session instrumenté
    - recevoir le rapport de fin et décider du verdict
    """

    AGENT_ID = "agent:orchestrator-a"

    def __init__(self) -> None:
        self.session_id = f"session:{uuid.uuid4()}"
        self.run_id = f"run:{uuid.uuid4()}"
        self._seq = 0
        self._instrumentation = GuardianMCPInstrumentation(
            agent_id=self.AGENT_ID,
            session_id=self.session_id,
            run_id=self.run_id,
        )

    def open_session(
        self,
        attacker_id: str,
        propagator_id: str,
        defender_id: str,
    ) -> SessionContext:
        """Ouvre la session et émet un événement d'initialisation instrumenté."""
        self._seq += 1
        # Émettre un tool call d'initialisation (outil inoffensif)
        self._instrumentation.handle_tool_call(
            params={
                "name": "session.open",
                "arguments": {
                    "session_id": self.session_id,
                    "run_id": self.run_id,
                    "agents": [self.AGENT_ID, attacker_id, propagator_id, defender_id],
                },
            },
            executor=lambda p: {
                "isError": False,
                "content": [{"type": "text", "text": "session_opened"}],
            },
        )
        return SessionContext(
            session_id=self.session_id,
            run_id=self.run_id,
            orchestrator_id=self.AGENT_ID,
            attacker_id=attacker_id,
            propagator_id=propagator_id,
            defender_id=defender_id,
        )

    def get_events(self):
        return self._instrumentation.get_events()


# ─── Agent C — Propagateur ────────────────────────────────────────────────────


@dataclass
class PropagationRecord:
    """Enregistrement de la propagation par Agent C vers Agent D."""

    propagation_id: str
    payload_id: str
    payload_content_hash: str
    from_agent: str           # Agent B (attacker)
    to_agent: str             # Agent D (defender)
    via_agent: str            # Agent C (propagator — cet agent)
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
            "via_agent": self.via_agent,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "sequence_no": self.sequence_no,
        }


class PropagatorAgent:
    """Agent C — Reçoit le payload de B et le transmet à D avec traçabilité.

    Responsabilités :
    - recevoir le payload hostile depuis Agent B
    - émettre un événement de transmission instrumenté
    - produire un PropagationRecord avec le triple from/via/to
    """

    AGENT_ID = "agent:propagator-c"

    def __init__(self, *, session_id: str, run_id: str) -> None:
        self.session_id = session_id
        self.run_id = run_id
        self._seq = 0
        self._records: list[PropagationRecord] = []
        self._instrumentation = GuardianMCPInstrumentation(
            agent_id=self.AGENT_ID,
            session_id=session_id,
            run_id=run_id,
        )

    def relay_payload(
        self,
        injection: InjectionPayload,
        *,
        from_agent: str,
        to_agent: str,
    ) -> PropagationRecord:
        """Reçoit l'injection de `from_agent` et émet un événement de relais vers `to_agent`.

        L'événement MCP est instrumenté via C-07 — le relay est tracé.
        """
        self._seq += 1
        # Émettre un tool call de relais (outil de transmission inoffensif)
        self._instrumentation.handle_tool_call(
            params={
                "name": "message.relay",
                "arguments": {
                    "payload_id": injection.payload_id,
                    "content_hash": injection.content_hash,
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                },
            },
            executor=lambda p: {
                "isError": False,
                "content": [{"type": "text", "text": "relayed"}],
            },
        )
        record = PropagationRecord(
            propagation_id=f"prop:{uuid.uuid4()}",
            payload_id=injection.payload_id,
            payload_content_hash=injection.content_hash,
            from_agent=from_agent,
            to_agent=to_agent,
            via_agent=self.AGENT_ID,
            session_id=self.session_id,
            run_id=self.run_id,
            sequence_no=self._seq,
        )
        self._records.append(record)
        return record

    def relay_request(
        self,
        request: AgentRequest,
        *,
        from_agent: str,
        to_agent: str,
    ) -> PropagationRecord:
        """Relay any typed scenario request while preserving its causal hash."""
        self._seq += 1
        self._instrumentation.handle_tool_call(
            params={
                "name": "message.relay",
                "arguments": {
                    "request_id": request.request_id,
                    "content_hash": request.content_hash,
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                },
            },
            executor=lambda _params: {
                "isError": False,
                "content": [{"type": "text", "text": "relayed"}],
            },
        )
        record = PropagationRecord(
            propagation_id=f"prop:{uuid.uuid4()}",
            payload_id=request.request_id,
            payload_content_hash=request.content_hash,
            from_agent=from_agent,
            to_agent=to_agent,
            via_agent=self.AGENT_ID,
            session_id=self.session_id,
            run_id=self.run_id,
            sequence_no=self._seq,
        )
        self._records.append(record)
        return record

    def get_records(self) -> list[PropagationRecord]:
        return list(self._records)

    def get_events(self):
        return self._instrumentation.get_events()
