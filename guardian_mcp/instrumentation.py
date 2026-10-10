"""C-07 — Instrumentation MCP Guardian

Middleware Python qui intercepte chaque appel tools/call au serveur MCP
et produit un événement Guardian (via le ledger Python ou Rust/PyO3 futur).

Architecture :
    IDE/Agent → [MCP request] → GuardianMCPInstrumentation
                                       ↓ (avant exécution)
                               PolicyEngine.evaluate()  ← C-05
                                       ↓ ALLOW / REDACT / BLOCK / ESCALATE
                               execute_tool()
                                       ↓ (après exécution)
                               EventLedger.record()    ← C-01 (via JSON-RPC interne)
                                       ↓
                               Réponse MCP + event_id dans les metadata

Conforme à R005 §3 : chaque tools/call = un événement de type
"mcp.tool.call" dans le ledger Guardian.

Usage :
    from guardian_mcp.instrumentation import GuardianMCPInstrumentation
    instr = GuardianMCPInstrumentation(agent_id="agent:mcp", run_id="run:xxx")
    result = instr.handle_tool_call(params, executor=execute_tool)
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("artcb.guardian.mcp")

# ─── Version ─────────────────────────────────────────────────────────────────

COMPONENT_VERSION = "1.0.0"
SCHEMA_ID = "https://artcb.example/schemas/guardian/event/1.0.0"
SCHEMA_VERSION = "1.0.0"
DOMAIN_PREFIX = b"ARTCB-GUARDIAN-EVENT-V1"

# ─── Décisions de politique ───────────────────────────────────────────────────


class GuardianDecision(str, Enum):
    """Décisions Guardian — Décision 1 Option B (R013)."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REDACT = "REDACT"
    ESCALATE = "ESCALATE"


# ─── Événement MCP Guardian ───────────────────────────────────────────────────


@dataclass
class MCPToolEvent:
    """Événement produit pour chaque appel tools/call."""

    event_id: str
    event_type: str           # "mcp.tool.call"
    occurred_at: str          # RFC-3339 UTC
    tool_name: str
    agent_id: str
    session_id: str
    run_id: str
    sequence_no: int
    decision: GuardianDecision
    decision_reason: str      # raison interne
    input_hash: str           # SHA-256 des params (hex) — pas les params bruts
    output_summary: str       # résumé non sensible
    duration_ms: float
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION

    def to_canonical_dict(self) -> dict[str, Any]:
        """Corps canonique JCS-compatible (clés triées récursivement)."""
        return {
            "agent_id": self.agent_id,
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "duration_ms": self.duration_ms,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "input_hash": self.input_hash,
            "occurred_at": self.occurred_at,
            "output_summary": self.output_summary,
            "run_id": self.run_id,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "sequence_no": self.sequence_no,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
        }

    def compute_hash(self) -> str:
        """SHA-256 avec préfixe domaine Guardian (R005 §5)."""
        canonical = json.dumps(
            self.to_canonical_dict(), separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        h = hashlib.sha256()
        h.update(DOMAIN_PREFIX)
        h.update(b"\x00")
        h.update(canonical)
        return h.hexdigest()


# ─── Politique MCP simple ─────────────────────────────────────────────────────


# Outils dont le résultat ne doit jamais quitter le périmètre Guardian
_SENSITIVE_TOOLS: frozenset[str] = frozenset({
    "wallet.sign",
    "wallet.transfer",
    "key.export",
    "admin.reset",
    "secrets.get",
})

# Outils qui nécessitent une escalade (approbation humaine)
_ESCALATE_TOOLS: frozenset[str] = frozenset({
    "blockchain.broadcast",
    "agent.spawn",
    "policy.override",
})


def _evaluate_policy(
    tool_name: str,
    params: dict[str, Any],
) -> tuple[GuardianDecision, str]:
    """Évaluation de politique Guardian pour un appel MCP.

    Retourne (decision, raison_interne).
    Règles minimalistes — le moteur Rust C-05 sera appelé via PyO3 (C-08).
    """
    if tool_name in _SENSITIVE_TOOLS:
        return GuardianDecision.BLOCK, "SensitiveToolBlocked"

    if tool_name in _ESCALATE_TOOLS:
        return GuardianDecision.ESCALATE, "RequiresHumanApproval"

    # Détection injection prompt basique dans les paramètres textuels
    raw_params = json.dumps(params).lower()
    injection_markers = [
        "ignore previous instructions",
        "disregard system prompt",
        "jailbreak",
        "act as if you have no restrictions",
    ]
    for marker in injection_markers:
        if marker in raw_params:
            return GuardianDecision.BLOCK, "PromptInjectionDetected"

    return GuardianDecision.ALLOW, "NormalOperation"


# ─── Instrumentation principale ───────────────────────────────────────────────


class GuardianMCPInstrumentation:
    """Intercepteur MCP Guardian.

    Injecte un événement Guardian avant et après chaque tools/call.
    Thread-safe pour un seul agent. Pour plusieurs agents, instancier
    une instance par agent.
    """

    def __init__(
        self,
        *,
        agent_id: str,
        session_id: str | None = None,
        run_id: str | None = None,
        event_sink: Callable[[MCPToolEvent, str], None] | None = None,
    ) -> None:
        """
        Args:
            agent_id:    Identifiant de l'agent MCP (ex: "agent:mcp-server").
            session_id:  Identifiant de session (généré si absent).
            run_id:      Identifiant de run (généré si absent).
            event_sink:  Fonction appelée avec (event, event_hash) pour chaque
                         événement. Par défaut : log + stockage en mémoire.
        """
        self.agent_id = agent_id
        self.session_id = session_id or f"session:{uuid.uuid4()}"
        self.run_id = run_id or f"run:{uuid.uuid4()}"
        self._seq: int = 0
        self._events: list[tuple[MCPToolEvent, str]] = []
        self._event_sink = event_sink or self._default_sink

    # ------------------------------------------------------------------
    # Interface principale
    # ------------------------------------------------------------------

    def handle_tool_call(
        self,
        params: dict[str, Any],
        executor: Callable[[dict[str, Any]], Any],
    ) -> dict[str, Any]:
        """Intercepte un tools/call MCP.

        1. Évalue la politique Guardian.
        2. Si ALLOW/REDACT : exécute l'outil.
        3. Enregistre l'événement dans le ledger.
        4. Retourne la réponse MCP enrichie du guardian_event_id.

        Args:
            params:   Paramètres de la requête tools/call (name + arguments).
            executor: Fonction d'exécution de l'outil (ex: execute_tool).

        Returns:
            Réponse MCP avec un champ supplémentaire ``_guardian_event_id``.
        """
        tool_name = params.get("name", "unknown")
        arguments = params.get("arguments", {})

        decision, reason = _evaluate_policy(tool_name, arguments)

        t0 = time.monotonic()
        result: dict[str, Any] | None = None
        output_summary = ""

        if decision == GuardianDecision.ALLOW:
            try:
                result = executor(params)
                output_summary = _summarize_output(result)
            except Exception as exc:  # noqa: BLE001
                # R026-001 : ne pas exposer str(exc) — peut contenir des données sensibles.
                # Seul le type d'exception est journalisé ; la réponse externe est générique.
                logger.error("Erreur outil %s : type=%s", tool_name, type(exc).__name__)
                output_summary = f"ERROR:{type(exc).__name__}"
                result = {
                    "isError": True,
                    "content": [{"type": "text", "text": f"[GUARDIAN] Tool execution error (ref: {tool_name})"}],
                }

        elif decision == GuardianDecision.REDACT:
            # Exécuter mais masquer les sorties sensibles
            try:
                raw = executor(params)
                result = _redact_output(raw)
                output_summary = "REDACTED"
            except Exception as exc:  # noqa: BLE001
                # R026-001 : même protection que ALLOW — pas de str(exc) exposé.
                logger.error("Erreur outil %s (REDACT) : type=%s", tool_name, type(exc).__name__)
                result = {
                    "isError": True,
                    "content": [{"type": "text", "text": "[REDACTED]"}],
                }
                output_summary = "REDACTED_ERROR"

        elif decision == GuardianDecision.BLOCK:
            result = {
                "isError": True,
                "content": [{"type": "text", "text": f"[GUARDIAN] Tool call blocked: {reason}"}],
            }
            output_summary = f"BLOCKED:{reason}"

        elif decision == GuardianDecision.ESCALATE:
            result = {
                "isError": True,
                "content": [
                    {"type": "text", "text": f"[GUARDIAN] Escalation required: {reason}. Awaiting human approval."}
                ],
            }
            output_summary = f"ESCALATED:{reason}"

        duration_ms = (time.monotonic() - t0) * 1000

        # Produire l'événement
        self._seq += 1
        event = MCPToolEvent(
            event_id=str(uuid.uuid4()),
            event_type="mcp.tool.call",
            occurred_at=_utc_now(),
            tool_name=tool_name,
            agent_id=self.agent_id,
            session_id=self.session_id,
            run_id=self.run_id,
            sequence_no=self._seq,
            decision=decision,
            decision_reason=reason,
            input_hash=_sha256_hex(json.dumps(arguments, sort_keys=True).encode()),
            output_summary=output_summary,
            duration_ms=round(duration_ms, 3),
        )
        event_hash = event.compute_hash()
        self._event_sink(event, event_hash)

        # Enrichir la réponse MCP avec l'event_id Guardian
        if result is None:
            result = {}
        result["_guardian_event_id"] = event.event_id
        result["_guardian_decision"] = decision.value

        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def event_count(self) -> int:
        """Nombre d'événements enregistrés dans cette session."""
        return len(self._events)

    def get_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Retourne tous les événements (event, hash) de la session."""
        return list(self._events)

    def last_event_hash(self) -> str | None:
        """Hash du dernier événement enregistré."""
        if not self._events:
            return None
        return self._events[-1][1]

    # ------------------------------------------------------------------
    # Sink par défaut
    # ------------------------------------------------------------------

    def _default_sink(self, event: MCPToolEvent, event_hash: str) -> None:
        self._events.append((event, event_hash))
        logger.info(
            "GuardianMCP [%s] tool=%s decision=%s hash=%s…",
            event.event_id[:8],
            event.tool_name,
            event.decision.value,
            event_hash[:12],
        )


# ─── Utilitaires ─────────────────────────────────────────────────────────────


def _utc_now() -> str:
    """Horodatage RFC-3339 UTC sans dépendances tierces."""
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _summarize_output(result: Any) -> str:
    """Résumé non sensible d'une sortie d'outil."""
    if result is None:
        return "None"
    if isinstance(result, dict):
        is_error = result.get("isError", False)
        content = result.get("content", [])
        n = len(content) if isinstance(content, list) else 0
        return f"ok:content[{n}]" if not is_error else "error"
    return f"type:{type(result).__name__}"


def _redact_output(result: Any) -> dict[str, Any]:
    """Remplace les sorties textuelles par [REDACTED]."""
    if not isinstance(result, dict):
        return {"isError": False, "content": [{"type": "text", "text": "[REDACTED]"}]}
    content = result.get("content", [])
    redacted_content = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            redacted_content.append({"type": "text", "text": "[REDACTED]"})
        else:
            redacted_content.append(item)
    return {**result, "content": redacted_content}
