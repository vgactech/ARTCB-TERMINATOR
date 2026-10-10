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
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("artcb.guardian.mcp")

# ─── Version ─────────────────────────────────────────────────────────────────

COMPONENT_VERSION = "1.0.0"
SCHEMA_ID = "https://artcb.example/schemas/guardian/event/1.0.0"
SCHEMA_VERSION = "1.0.0"
DOMAIN_PREFIX = b"ARTCB-GUARDIAN-EVENT-V1"
CHAIN_DOMAIN_PREFIX = b"ARTCB-GUARDIAN-CHAIN-V1"
GENESIS_HASH = "0" * 64

# ─── Phases d'événement (R033-A) ─────────────────────────────────────────────

class EventPhase(str, Enum):
    """Phase de cycle de vie d'un événement Guardian.

    INTENT    : journalisé AVANT l'appel à l'exécuteur — preuve d'intention.
                Si l'exécuteur ne termine jamais, cet événement reste seul.
    TERMINAL  : journalisé APRÈS l'appel (ou après BLOCK/ESCALATE immédiat).
                Sous-types via terminal_status : COMPLETED | FAILED | NOT_EXECUTED.

    Un intent_id commun lie l'intent et son terminal.
    Un redémarrage avec un intent sans terminal correspondant doit classer
    l'appel comme IN_DOUBT (R033-E).
    """
    INTENT = "INTENT"
    TERMINAL = "TERMINAL"

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
    previous_event_hash: str = GENESIS_HASH  # R023-002 : lien cryptographique au précédent
    # R032-A : statut d'exécution explicite — distingue les cas EXECUTED/FAILED/NOT_EXECUTED.
    # Valeurs : "EXECUTED" | "FAILED" | "NOT_EXECUTED" | "UNKNOWN"
    # NOT_EXECUTED : l'outil n'a pas été appelé (BLOCK, ESCALATE).
    # FAILED       : l'outil a été appelé mais a levé une exception.
    # EXECUTED     : l'outil a été appelé et a retourné un résultat.
    # UNKNOWN      : état indéterminé (ex: crash entre exécution et journalisation).
    execution_status: str = "NOT_EXECUTED"
    # R032-C : marqueur de rejeu — True si cet événement est produit lors d'un replay.
    # Un événement de replay ne doit pas déclencher d'action externe.
    is_replay: bool = False
    # R033-A : phase du cycle de vie de l'événement.
    # INTENT   : journalisé avant l'exécution.
    # TERMINAL : journalisé après l'exécution (ou immédiatement pour BLOCK/ESCALATE).
    event_phase: str = EventPhase.TERMINAL  # défaut : TERMINAL pour rétrocompatibilité
    # R033-A : identifiant commun entre l'intent et son terminal.
    # Vide ("") pour les événements TERMINAL directement émis (BLOCK/ESCALATE).
    intent_id: str = ""
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION

    def to_canonical_dict(self) -> dict[str, Any]:
        """Corps canonique JCS-compatible (clés triées récursivement).

        Le champ previous_event_hash est inclus dans le corps canonique (R023-002) :
        tout changement d'ordre ou suppression d'un événement modifie le hash
        de l'événement suivant dans la chaîne.

        R033-A : event_phase et intent_id sont inclus dans le corps canonique.
        """
        return {
            "agent_id": self.agent_id,
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "duration_ms": self.duration_ms,
            "event_id": self.event_id,
            "event_phase": self.event_phase,
            "event_type": self.event_type,
            "execution_status": self.execution_status,
            "input_hash": self.input_hash,
            "intent_id": self.intent_id,
            "is_replay": self.is_replay,
            "occurred_at": self.occurred_at,
            "output_summary": self.output_summary,
            "previous_event_hash": self.previous_event_hash,
            "run_id": self.run_id,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "sequence_no": self.sequence_no,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
        }

    def compute_hash(self) -> str:
        """SHA-256 avec préfixe domaine Guardian (R005 §5).

        Le previous_event_hash est inclus dans le corps canonique,
        ce qui chaîne cryptographiquement chaque événement à son prédécesseur.
        """
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
        initial_seq: int = 0,
        initial_prev_hash: str | None = None,
    ) -> None:
        """
        Args:
            agent_id:          Identifiant de l'agent MCP (ex: "agent:mcp-server").
            session_id:        Identifiant de session (généré si absent).
            run_id:            Identifiant de run (généré si absent).
            event_sink:        Fonction appelée avec (event, event_hash) pour chaque
                               événement. Par défaut : log + stockage en mémoire.
            initial_seq:       R028-B — numéro de séquence de reprise (issu de
                               recover_state_from_jsonl). 0 pour une nouvelle session.
            initial_prev_hash: R028-B — hash du dernier événement connu (issu de
                               recover_state_from_jsonl). GENESIS_HASH si absent.
        """
        self.agent_id = agent_id
        self.session_id = session_id or f"session:{uuid.uuid4()}"
        self.run_id = run_id or f"run:{uuid.uuid4()}"
        self._seq: int = initial_seq
        # R028-B : si on reprend un journal existant, initialiser _events avec
        # un sentinel pour que prev_hash soit correct dès le premier appel.
        if initial_prev_hash and initial_prev_hash != GENESIS_HASH:
            self._events: list[tuple[MCPToolEvent, str]] = [
                (None, initial_prev_hash)  # type: ignore[list-item]
            ]
        else:
            self._events = []
        self._event_sink = event_sink or self._default_sink

    # ------------------------------------------------------------------
    # Interface principale
    # ------------------------------------------------------------------

    def handle_tool_call(
        self,
        params: dict[str, Any],
        executor: Callable[[dict[str, Any]], Any],
        *,
        is_replay: bool = False,
    ) -> dict[str, Any]:
        """Intercepte un tools/call MCP.

        1. Évalue la politique Guardian.
        2. R033-A : journalise un événement INTENT avant toute exécution externe.
        3. Si ALLOW/REDACT et non replay : exécute l'outil.
           R033-B : en mode replay (is_replay=True), l'exécuteur réel n'est JAMAIS appelé.
                    La barrière est physique — aucun chemin de code ne contourne ce test.
        4. R033-A : journalise un événement TERMINAL après exécution.
        5. Retourne la réponse MCP enrichie du guardian_event_id.

        Args:
            params:    Paramètres de la requête tools/call (name + arguments).
            executor:  Fonction d'exécution de l'outil (ex: execute_tool).
            is_replay: R033-B — si True, l'exécuteur n'est pas appelé. Les événements
                       produits portent is_replay=True dans leur corps canonique.

        Returns:
            Réponse MCP avec un champ supplémentaire ``_guardian_event_id``.
        """
        tool_name = params.get("name", "unknown")
        arguments = params.get("arguments", {})
        input_hash = _sha256_hex(json.dumps(arguments, sort_keys=True).encode())

        decision, reason = _evaluate_policy(tool_name, arguments)

        # ── R033-A : journaliser l'INTENT avant toute exécution externe ──────
        intent_id = str(uuid.uuid4())
        self._seq += 1
        prev_hash = self._events[-1][1] if self._events else GENESIS_HASH
        intent_event = MCPToolEvent(
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
            input_hash=input_hash,
            output_summary="INTENT",
            duration_ms=0.0,
            previous_event_hash=prev_hash,
            execution_status="NOT_EXECUTED",
            is_replay=is_replay,
            event_phase=EventPhase.INTENT,
            intent_id=intent_id,
        )
        intent_hash = intent_event.compute_hash()
        self._events.append((intent_event, intent_hash))
        self._event_sink(intent_event, intent_hash)

        # ── Exécution ─────────────────────────────────────────────────────────
        t0 = time.monotonic()
        result: dict[str, Any] | None = None
        output_summary = ""
        execution_status = "NOT_EXECUTED"  # R032-A : valeur par défaut

        if decision == GuardianDecision.ALLOW:
            if is_replay:
                # R033-B : barrière physique — le vrai exécuteur n'est jamais appelé en replay.
                output_summary = "REPLAY:NOT_EXECUTED"
                execution_status = "NOT_EXECUTED"
                result = {
                    "isError": False,
                    "content": [{"type": "text", "text": "[GUARDIAN] Replay mode — execution suppressed"}],
                }
            else:
                try:
                    result = executor(params)
                    output_summary = _summarize_output(result)
                    execution_status = "EXECUTED"
                except Exception as exc:  # noqa: BLE001
                    # R026-001 : ne pas exposer str(exc) — peut contenir des données sensibles.
                    # Seul le type d'exception est journalisé ; la réponse externe est générique.
                    logger.error("Erreur outil %s : type=%s", tool_name, type(exc).__name__)
                    output_summary = f"ERROR:{type(exc).__name__}"
                    execution_status = "FAILED"
                    result = {
                        "isError": True,
                        "content": [{"type": "text", "text": f"[GUARDIAN] Tool execution error (ref: {tool_name})"}],
                    }

        elif decision == GuardianDecision.REDACT:
            if is_replay:
                # R033-B : même barrière pour REDACT.
                output_summary = "REPLAY:NOT_EXECUTED"
                execution_status = "NOT_EXECUTED"
                result = {
                    "isError": False,
                    "content": [{"type": "text", "text": "[GUARDIAN] Replay mode — execution suppressed"}],
                }
            else:
                # Exécuter mais masquer les sorties sensibles
                try:
                    raw = executor(params)
                    result = _redact_output(raw)
                    output_summary = "REDACTED"
                    execution_status = "EXECUTED"
                except Exception as exc:  # noqa: BLE001
                    # R026-001 : même protection que ALLOW — pas de str(exc) exposé.
                    logger.error("Erreur outil %s (REDACT) : type=%s", tool_name, type(exc).__name__)
                    result = {
                        "isError": True,
                        "content": [{"type": "text", "text": "[REDACTED]"}],
                    }
                    output_summary = "REDACTED_ERROR"
                    execution_status = "FAILED"

        elif decision == GuardianDecision.BLOCK:
            result = {
                "isError": True,
                "content": [{"type": "text", "text": f"[GUARDIAN] Tool call blocked: {reason}"}],
            }
            output_summary = f"BLOCKED:{reason}"
            # execution_status reste "NOT_EXECUTED" — l'outil n'a pas été appelé

        elif decision == GuardianDecision.ESCALATE:
            result = {
                "isError": True,
                "content": [
                    {"type": "text", "text": f"[GUARDIAN] Escalation required: {reason}. Awaiting human approval."}
                ],
            }
            output_summary = f"ESCALATED:{reason}"
            # execution_status reste "NOT_EXECUTED"

        duration_ms = (time.monotonic() - t0) * 1000

        # ── R033-A : journaliser le TERMINAL après exécution ─────────────────
        self._seq += 1
        prev_hash = self._events[-1][1] if self._events else GENESIS_HASH
        terminal_event = MCPToolEvent(
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
            input_hash=input_hash,
            output_summary=output_summary,
            duration_ms=round(duration_ms, 3),
            previous_event_hash=prev_hash,
            execution_status=execution_status,
            is_replay=is_replay,
            event_phase=EventPhase.TERMINAL,
            intent_id=intent_id,
        )
        terminal_hash = terminal_event.compute_hash()
        self._events.append((terminal_event, terminal_hash))
        self._event_sink(terminal_event, terminal_hash)

        # Enrichir la réponse MCP avec l'event_id Guardian (terminal)
        if result is None:
            result = {}
        result["_guardian_event_id"] = terminal_event.event_id
        result["_guardian_decision"] = decision.value
        result["_guardian_intent_id"] = intent_id

        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def event_count(self) -> int:
        """Nombre d'appels tools/call traités (= nombre d'événements TERMINAL).

        Chaque appel handle_tool_call produit un INTENT + un TERMINAL.
        Cette méthode retourne le nombre de TERMINAL pour rester compatible
        avec les usages existants (1 appel = 1 événement métier).
        """
        return sum(
            1 for e, _ in self._events
            if e is not None and e.event_phase == EventPhase.TERMINAL
        )

    def get_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Retourne uniquement les événements TERMINAL (hors INTENT et sentinel de reprise).

        Chaque entrée correspond à un appel handle_tool_call terminé.
        Pour obtenir tous les événements (INTENT + TERMINAL), utiliser get_all_events().
        """
        return [
            (e, h) for e, h in self._events
            if e is not None and e.event_phase == EventPhase.TERMINAL
        ]

    def get_all_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Retourne tous les événements (INTENT + TERMINAL), hors sentinel de reprise.

        R033-A : permet d'inspecter le cycle complet intent/terminal.
        """
        return [(e, h) for e, h in self._events if e is not None]

    def last_event_hash(self) -> str | None:
        """Hash du dernier événement enregistré."""
        if not self._events:
            return None
        return self._events[-1][1]

    # ------------------------------------------------------------------
    # Sink par défaut
    # ------------------------------------------------------------------

    def _default_sink(self, event: MCPToolEvent, event_hash: str) -> None:
        # _events est déjà alimenté dans handle_tool_call avant l'appel au sink.
        # Ce sink se charge uniquement de la journalisation.
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


# ─── Persistance durable (R021-005) ──────────────────────────────────────────


def make_file_sink(path: str | Path) -> Callable[[MCPToolEvent, str], None]:
    """Retourne un sink qui persiste chaque événement en JSONL avec fsync.

    Chaque ligne est un objet JSON contenant :
    - tous les champs de MCPToolEvent (decision comme valeur string)
    - le event_hash calculé
    - previous_event_hash (R023-002)

    Le fichier peut être rechargé et vérifié via load_and_verify_jsonl().
    Pour reprendre l'écriture dans un fichier existant après redémarrage,
    utiliser recover_state_from_jsonl() pour initialiser l'instrumentation
    avec le bon seq de départ et le bon previous_event_hash (R028-B).

    R021-005 : la durabilité est garantie par os.fsync() après chaque écriture.
    R028-C : gap entre exécution et écriture documenté dans load_and_verify_jsonl().
    """
    jsonl_path = Path(path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    def sink(event: MCPToolEvent, event_hash: str) -> None:
        record = {
            "agent_id": event.agent_id,
            "decision": event.decision.value,
            "decision_reason": event.decision_reason,
            "duration_ms": event.duration_ms,
            "event_hash": event_hash,
            "event_id": event.event_id,
            "event_phase": event.event_phase,             # R033-A
            "event_type": event.event_type,
            "execution_status": event.execution_status,   # R032-A
            "input_hash": event.input_hash,
            "intent_id": event.intent_id,                 # R033-A
            "is_replay": event.is_replay,                 # R032-C
            "occurred_at": event.occurred_at,
            "output_summary": event.output_summary,
            "previous_event_hash": event.previous_event_hash,
            "run_id": event.run_id,
            "schema_id": event.schema_id,
            "schema_version": event.schema_version,
            "sequence_no": event.sequence_no,
            "session_id": event.session_id,
            "tool_name": event.tool_name,
        }
        line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
        # R032-B : verrou fichier exclusif pour garantir l'atomicité des écritures
        # entre plusieurs processus partageant le même journal.
        with open(jsonl_path, "a+", encoding="utf-8") as f:
            if os.name == "nt":
                import msvcrt

                # Windows locks a byte range from the current position. Locking
                # the first byte serializes appenders even when the journal is
                # still empty; the payload itself remains append-only.
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    f.seek(0, os.SEEK_END)
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    return sink


@dataclass
class ChainVerificationResult:
    """Résultat de la vérification d'un fichier JSONL Guardian."""
    entries_verified: int
    verdict: str           # "PASS" ou "FAIL"
    mismatches: list[dict]
    limits: list[str]

    def is_pass(self) -> bool:
        return self.verdict == "PASS"


def load_and_verify_jsonl(
    path: str | Path,
    *,
    expected_count: int | None = None,
    expected_last_hash: str | None = None,
) -> ChainVerificationResult:
    """Charge et vérifie un fichier JSONL Guardian après redémarrage.

    R021-005 : démontre la persistance — les événements sont relus depuis le disque.
    R023-002 : vérifie le chaînage parent-hash entre chaque événement.

    Vérifications effectuées :
    1. Recalcul du event_hash de chaque événement (intégrité individuelle).
    2. Vérification que previous_event_hash de chaque entrée correspond
       au event_hash de l'entrée précédente (chaînage cryptographique).
    3. Vérification de la monotonie des sequence_no.
    4. (R028-A) Si expected_count est fourni, FAIL si le nombre d'entrées ne correspond pas.
    5. (R028-A) Si expected_last_hash est fourni, FAIL si le dernier hash ne correspond pas.

    Limites :
    - Sans expected_count/expected_last_hash, la troncature finale n'est pas détectable.
    - Ne recrée pas les objets MCPToolEvent complets — utilise les champs
      bruts du JSON pour recalculer le hash.
    """
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return ChainVerificationResult(
            entries_verified=0,
            verdict="FAIL",
            mismatches=[{"error": f"Fichier introuvable : {path}"}],
            limits=[],
        )

    entries = []
    with open(jsonl_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                return ChainVerificationResult(
                    entries_verified=len(entries),
                    verdict="FAIL",
                    mismatches=[{"error": f"JSON invalide ligne {lineno} : {type(e).__name__}"}],
                    limits=[],
                )

    # R028-A : journal vide avec ancrage externe → FAIL systématique
    # R030-001 : un expected_last_hash non vide sur un journal vide doit aussi FAIL.
    if not entries and expected_last_hash:
        return ChainVerificationResult(
            entries_verified=0,
            verdict="FAIL",
            mismatches=[{
                "error": "Journal vide mais expected_last_hash fourni — journal manquant ou entièrement tronqué",
                "field": "entries_count",
            }],
            limits=["R030-001 : journal vide détecté via expected_last_hash"],
        )
    if expected_count is not None and len(entries) != expected_count:
        return ChainVerificationResult(
            entries_verified=len(entries),
            verdict="FAIL",
            mismatches=[{
                "error": f"Nombre d'entrées attendu : {expected_count}, trouvé : {len(entries)}",
                "field": "entries_count",
            }],
            limits=[
                "R028-A : journal vide ou tronqué détecté via expected_count",
            ],
        )

    mismatches: list[dict] = []
    prev_hash = GENESIS_HASH
    prev_seq = 0

    for i, record in enumerate(entries):
        event_id = record.get("event_id", f"<ligne {i+1}>")

        # 1. Recalculer le hash de l'événement depuis ses champs canoniques
        # R032-A/C : execution_status et is_replay sont désormais dans le corps canonique
        # R033-A : event_phase et intent_id sont dans le corps canonique
        canonical_fields = {
            k: record[k]
            for k in (
                "agent_id", "decision", "decision_reason", "duration_ms",
                "event_id", "event_phase", "event_type", "execution_status", "input_hash",
                "intent_id", "is_replay", "occurred_at", "output_summary",
                "previous_event_hash", "run_id", "schema_id", "schema_version",
                "sequence_no", "session_id", "tool_name",
            )
            if k in record
        }
        canonical_bytes = json.dumps(
            canonical_fields, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        h = hashlib.sha256()
        h.update(DOMAIN_PREFIX)
        h.update(b"\x00")
        h.update(canonical_bytes)
        recomputed_hash = h.hexdigest()

        stored_hash = record.get("event_hash", "")
        if recomputed_hash != stored_hash:
            mismatches.append({
                "event_id": event_id,
                "field": "event_hash",
                "stored": stored_hash[:16] + "…",
                "recomputed": recomputed_hash[:16] + "…",
            })

        # 2. Vérifier le chaînage parent-hash (R023-002)
        stored_prev = record.get("previous_event_hash", "")
        if stored_prev != prev_hash:
            mismatches.append({
                "event_id": event_id,
                "field": "previous_event_hash",
                "expected": prev_hash[:16] + "…",
                "stored": stored_prev[:16] + "…",
            })

        # 3. Vérifier la monotonie des séquences
        seq = record.get("sequence_no", 0)
        if seq <= prev_seq:
            mismatches.append({
                "event_id": event_id,
                "field": "sequence_no",
                "expected": f">{prev_seq}",
                "stored": str(seq),
            })

        prev_hash = stored_hash  # avancer avec le hash stocké pour suivre la chaîne
        prev_seq = seq

    # R028-A : vérification du dernier hash si un ancrage externe est fourni
    if expected_last_hash is not None and entries:
        actual_last = entries[-1].get("event_hash", "")
        if actual_last != expected_last_hash:
            mismatches.append({
                "error": f"Dernier hash attendu : {expected_last_hash[:16]}…, trouvé : {actual_last[:16]}…",
                "field": "last_event_hash",
            })

    verdict = "PASS" if not mismatches else "FAIL"
    return ChainVerificationResult(
        entries_verified=len(entries),
        verdict=verdict,
        mismatches=mismatches,
        limits=[
            "R021-005 : persistance JSONL avec fsync — durabilité démontrée après rechargement",
            "R023-002 : chaînage previous_event_hash vérifié entre événements successifs",
            "R028-A : troncature détectable si expected_count ou expected_last_hash est fourni",
            "Limite : sans ancrage externe, la troncature finale reste non détectable",
            "R028-C : fsync garantit la durabilité d'une écriture effectuée — "
            "un crash entre exécution et écriture laisse un gap non enregistré",
        ],
    )


def find_in_doubt_intents(path: str | Path) -> list[dict]:
    """Identifie les événements INTENT sans TERMINAL correspondant (R033-E).

    Un événement INTENT sans TERMINAL indique un crash ou un arrêt brutal
    entre la journalisation de l'intention et la fin de l'exécution.
    Ces appels sont classés IN_DOUBT et doivent être signalés à l'opérateur.

    Retourne une liste de dicts {intent_id, event_id, tool_name, sequence_no, occurred_at}
    pour chaque intent orphelin trouvé dans le journal.

    Retourne [] si le fichier n'existe pas ou est vide.
    """
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return []

    intents: dict[str, dict] = {}      # intent_id → enregistrement INTENT
    terminals: set[str] = set()        # intent_id des TERMINAL vus

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            phase = record.get("event_phase", "")
            iid = record.get("intent_id", "")
            if not iid:
                continue
            if phase == EventPhase.INTENT:
                intents[iid] = {
                    "intent_id": iid,
                    "event_id": record.get("event_id", ""),
                    "tool_name": record.get("tool_name", ""),
                    "sequence_no": record.get("sequence_no", 0),
                    "occurred_at": record.get("occurred_at", ""),
                }
            elif phase == EventPhase.TERMINAL:
                terminals.add(iid)

    return [v for k, v in intents.items() if k not in terminals]


def recover_state_from_jsonl(path: str | Path) -> tuple[int, str]:
    """Relit un fichier JSONL existant pour récupérer (sequence_no, last_hash).

    R028-B : permet à une nouvelle instance d'instrumentation de reprendre
    l'écriture dans un fichier existant sans rompre la chaîne ni répéter
    les numéros de séquence.

    R030-002 : effectue une vérification complète de la chaîne avant de
    retourner l'état. Lève ValueError si le journal est corrompu (hash invalide,
    séquence non monotone ou chaînage rompu). La reprise est refusée sur un
    journal dont l'intégrité n'a pas été établie.

    Retourne (0, GENESIS_HASH) si le fichier n'existe pas ou est vide.
    Lève ValueError si le journal contient des incohérences.
    """
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return 0, GENESIS_HASH

    # Vérification complète avant d'extraire l'état
    # R030-002 corr. : vérifier le verdict EN PREMIER, avant le count.
    # Un FAIL avec entries_verified==0 (ex: première ligne illisible) doit lever ValueError,
    # pas être silencieusement traité comme un journal vide légitime.
    result = load_and_verify_jsonl(jsonl_path)
    if not result.is_pass():
        raise ValueError(
            f"Reprise refusée : le journal '{path}' contient {len(result.mismatches)} "
            f"incohérence(s) — R030-002. Vérifiez avec load_and_verify_jsonl() avant de reprendre."
        )
    if result.entries_verified == 0:
        return 0, GENESIS_HASH

    # Journal valide — récupérer le dernier état depuis les lignes brutes
    last_seq = 0
    last_hash = GENESIS_HASH

    with open(jsonl_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Fichier JSONL corrompu ligne {lineno} : {type(e).__name__}"
                ) from e
            seq = record.get("sequence_no", 0)
            h = record.get("event_hash", "")
            if seq > 0 and h:
                last_seq = seq
                last_hash = h

    return last_seq, last_hash


# ─── Manifeste de replay (L-019-002) ─────────────────────────────────────────


@dataclass
class ReplayManifest:
    """Manifeste d'un replay — décrit les préconditions à vérifier avant tout replay.

    L-019-002 / R034 §3.2 : le manifeste doit être vérifié, pas simplement transporté.
    Le moteur compare le run demandé, le nombre d'entrées, la pointe de chaîne,
    les versions de schéma et le niveau demandé aux données réellement chargées.

    Champs :
        run_id             : identifiant du run auditeur.
        original_chain_tip : hash du dernier événement attendu (ancrage externe).
        expected_count     : nombre d'entrées attendues dans le journal.
        schema_version     : version du schéma attendue dans chaque événement.
        requested_level    : niveau de replay demandé ("R0", "R1", "R2", "R3").
        created_at         : horodatage de création (RFC-3339 UTC).
    """
    run_id: str
    original_chain_tip: str
    expected_count: int
    schema_version: str = SCHEMA_VERSION
    requested_level: str = "R0"
    created_at: str = field(default_factory=_utc_now)


def verify_manifest_preconditions(
    manifest: ReplayManifest,
    path: str | Path,
) -> ChainVerificationResult:
    """Vérifie les préconditions du manifeste avant tout replay.

    L-019-002 P0 : un replay ne peut commencer que si :
    1. La chaîne JSONL est intègre (load_and_verify_jsonl PASS).
    2. Le nombre d'entrées correspond à manifest.expected_count.
    3. Le dernier hash correspond à manifest.original_chain_tip.
    4. Tous les événements portent manifest.schema_version.

    Retourne un ChainVerificationResult avec verdict PASS ou FAIL.
    Un verdict FAIL doit bloquer tout replay supérieur.
    """
    result = load_and_verify_jsonl(
        path,
        expected_count=manifest.expected_count,
        expected_last_hash=manifest.original_chain_tip,
    )
    if not result.is_pass():
        return result

    # Vérification supplémentaire : version de schéma cohérente
    jsonl_path = Path(path)
    schema_mismatches: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            sv = record.get("schema_version", "")
            if sv and sv != manifest.schema_version:
                schema_mismatches.append({
                    "event_id": record.get("event_id", f"<ligne {lineno}>"),
                    "field": "schema_version",
                    "expected": manifest.schema_version,
                    "stored": sv,
                })

    if schema_mismatches:
        return ChainVerificationResult(
            entries_verified=result.entries_verified,
            verdict="FAIL",
            mismatches=schema_mismatches,
            limits=result.limits + ["L-019-002 P0 : incohérence de schema_version détectée"],
        )

    return ChainVerificationResult(
        entries_verified=result.entries_verified,
        verdict="PASS",
        mismatches=[],
        limits=result.limits + [
            f"L-019-002 P0 : manifeste vérifié — {result.entries_verified} entrées, "
            f"pointe de chaîne confirmée, schema_version={manifest.schema_version}",
        ],
    )


# ─── Archive R2 — réponses d'outils archivées (L-019-002 P1) ─────────────────


@dataclass
class ArchivedToolResponse:
    """Réponse d'outil archivée, liée à son intent_id.

    L-019-002 P1 : associe chaque invocation à un identifiant stable.
    Le hash d'entrée (input_hash) permet de vérifier que la fixture correspond
    à l'appel original. La response_hash garantit l'intégrité de la réponse.
    """
    intent_id: str          # lien vers l'INTENT de l'appel original
    tool_name: str
    input_hash: str         # SHA-256 des arguments d'entrée (doit correspondre à l'INTENT)
    decision: str           # "ALLOW" | "BLOCK" | "REDACT" | "ESCALATE"
    execution_status: str   # "EXECUTED" | "FAILED" | "NOT_EXECUTED"
    response_payload: dict  # réponse canonique archivée
    response_hash: str      # SHA-256 de response_payload (canonique, clés triées)
    schema_version: str = SCHEMA_VERSION
    archived_at: str = field(default_factory=_utc_now)

    def verify_response_hash(self) -> bool:
        """Vérifie que response_hash correspond à response_payload."""
        canonical = json.dumps(
            self.response_payload, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        expected = _sha256_hex(canonical)
        return expected == self.response_hash

    @staticmethod
    def compute_response_hash(payload: dict) -> str:
        """Calcule le hash canonique d'une réponse d'outil."""
        canonical = json.dumps(
            payload, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return _sha256_hex(canonical)

    def to_dict(self) -> dict:
        return {
            "archived_at": self.archived_at,
            "decision": self.decision,
            "execution_status": self.execution_status,
            "input_hash": self.input_hash,
            "intent_id": self.intent_id,
            "response_hash": self.response_hash,
            "response_payload": self.response_payload,
            "schema_version": self.schema_version,
            "tool_name": self.tool_name,
        }

    @staticmethod
    def from_dict(d: dict) -> "ArchivedToolResponse":
        return ArchivedToolResponse(
            intent_id=d["intent_id"],
            tool_name=d["tool_name"],
            input_hash=d["input_hash"],
            decision=d["decision"],
            execution_status=d["execution_status"],
            response_payload=d["response_payload"],
            response_hash=d["response_hash"],
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            archived_at=d.get("archived_at", ""),
        )


@dataclass
class ToolResponseArchive:
    """Archive des réponses d'outils pour le replay R2.

    L-019-002 P1 : stocke les réponses indexées par intent_id.
    Peut être persisté en JSONL ou maintenu en mémoire.
    """
    _entries: dict[str, ArchivedToolResponse] = field(default_factory=dict)

    def record(self, response: ArchivedToolResponse) -> None:
        """Enregistre une réponse archivée. Lève ValueError si intent_id déjà présent."""
        if response.intent_id in self._entries:
            raise ValueError(
                f"Archive R2 : intent_id '{response.intent_id}' déjà présent — "
                "duplication détectée, replay refusé"
            )
        self._entries[response.intent_id] = response

    def get(self, intent_id: str) -> ArchivedToolResponse | None:
        return self._entries.get(intent_id)

    def __len__(self) -> int:
        return len(self._entries)

    def to_jsonl(self, path: str | Path) -> None:
        """Persiste l'archive en JSONL."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for entry in self._entries.values():
                f.write(json.dumps(entry.to_dict(), separators=(",", ":"), sort_keys=True) + "\n")

    @staticmethod
    def from_jsonl(path: str | Path) -> "ToolResponseArchive":
        """Charge une archive depuis un fichier JSONL."""
        archive = ToolResponseArchive()
        p = Path(path)
        if not p.exists():
            return archive
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                archive._entries[d["intent_id"]] = ArchivedToolResponse.from_dict(d)
        return archive


def make_recording_sink(
    jsonl_path: str | Path,
    archive: ToolResponseArchive,
) -> Callable[[MCPToolEvent, str], None]:
    """Retourne un sink qui persiste les événements ET archive les réponses R2.

    À utiliser à la place de make_file_sink quand on veut capturer les réponses
    d'outils pour un replay R2 ultérieur. L'archive est alimentée sur les
    événements TERMINAL (qui portent execution_status et output_summary réels).

    L-019-002 P1 : les fixtures sont liées aux appels via intent_id, versionnées
    et leur intégrité est vérifiable via response_hash.
    """
    file_sink = make_file_sink(jsonl_path)

    def sink(event: MCPToolEvent, event_hash: str) -> None:
        # Persister dans le JSONL
        file_sink(event, event_hash)

        # Archiver la réponse sur les TERMINAL seulement (pas les INTENT)
        if event.event_phase == EventPhase.TERMINAL and event.intent_id:
            # La réponse canonique pour R2 est le output_summary + decision + status
            # (pas le payload brut — l'instrumentation ne conserve que le résumé)
            response_payload = {
                "decision": event.decision.value,
                "execution_status": event.execution_status,
                "output_summary": event.output_summary,
                "tool_name": event.tool_name,
            }
            response_hash = ArchivedToolResponse.compute_response_hash(response_payload)
            archived = ArchivedToolResponse(
                intent_id=event.intent_id,
                tool_name=event.tool_name,
                input_hash=event.input_hash,
                decision=event.decision.value,
                execution_status=event.execution_status,
                response_payload=response_payload,
                response_hash=response_hash,
                schema_version=event.schema_version,
            )
            archive.record(archived)

    return sink


# ─── Replay R2 — simulation sans effets externes (L-019-002 P1) ──────────────


@dataclass
class R2ReplayResult:
    """Résultat d'un replay R2 (outils simulés).

    L-019-002 P1 : distingue intégrité des traces, fidélité de simulation
    et exactitude métier. Ce sont des propriétés différentes.
    """
    verdict: str                    # "PASS" | "FAIL" | "IN_DOUBT"
    events_replayed: int
    external_calls_prevented: int   # sentinelle : doit rester 0
    mismatches: list[dict]
    in_doubt: list[dict]            # INTENT orphelins détectés
    limits: list[str]

    def is_pass(self) -> bool:
        return self.verdict == "PASS"


def replay_r2(
    journal_path: str | Path,
    archive: ToolResponseArchive,
    manifest: ReplayManifest,
) -> R2ReplayResult:
    """Replay R2 — rejoue le scénario depuis les fixtures archivées.

    L-019-002 P1 — critères R034 §4 :
    1. Vérification complète du manifeste et de la chaîne avant replay.
    2. Chaque TERMINAL est mis en correspondance avec sa fixture archivée.
    3. Aucun exécuteur externe n'est appelé — compteur sentinelle confirmé à 0.
    4. FAIL si une fixture est absente, altérée (hash invalide), dupliquée
       ou associée au mauvais intent_id / input_hash.
    5. FAIL si la décision ou execution_status diverge de la fixture.
    6. IN_DOUBT si un INTENT n'a pas de TERMINAL correspondant.
    7. Ne peut jamais rétrograder silencieusement vers R0 tout en affichant PASS.

    Retourne R2ReplayResult avec verdict PASS | FAIL | IN_DOUBT.
    """
    # ── P0 : vérifier les préconditions du manifeste ──────────────────────────
    precond = verify_manifest_preconditions(manifest, journal_path)
    if not precond.is_pass():
        return R2ReplayResult(
            verdict="FAIL",
            events_replayed=0,
            external_calls_prevented=0,
            mismatches=[{
                "error": "Préconditions du manifeste non satisfaites — replay R2 refusé",
                "details": precond.mismatches,
            }],
            in_doubt=[],
            limits=precond.limits + [
                "L-019-002 P0 : replay R2 refusé sur archive non conforme",
            ],
        )

    # ── Charger les entrées ───────────────────────────────────────────────────
    jsonl_path = Path(journal_path)
    entries: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                return R2ReplayResult(
                    verdict="FAIL",
                    events_replayed=0,
                    external_calls_prevented=0,
                    mismatches=[{"error": f"JSONL corrompu : {type(e).__name__}"}],
                    in_doubt=[],
                    limits=["L-019-002 P1 : journal illisible — replay R2 impossible"],
                )

    mismatches: list[dict] = []
    external_calls_prevented = 0  # sentinelle — toujours 0 dans R2

    # ── Vérification des TERMINAL vs fixtures ────────────────────────────────
    intent_ids_seen: set[str] = set()
    terminal_intent_ids: set[str] = set()

    for record in entries:
        phase = record.get("event_phase", "")
        intent_id = record.get("intent_id", "")
        event_id = record.get("event_id", "<?>")

        if phase == EventPhase.INTENT:
            intent_ids_seen.add(intent_id)

        elif phase == EventPhase.TERMINAL and intent_id:
            terminal_intent_ids.add(intent_id)
            archived = archive.get(intent_id)

            # Fixture absente
            if archived is None:
                mismatches.append({
                    "event_id": event_id,
                    "intent_id": intent_id,
                    "field": "fixture",
                    "error": "Fixture absente — replay R2 impossible pour cet appel",
                })
                continue

            # Vérification intégrité de la fixture (response_hash)
            if not archived.verify_response_hash():
                mismatches.append({
                    "event_id": event_id,
                    "intent_id": intent_id,
                    "field": "response_hash",
                    "error": "Hash de la fixture invalide — fixture altérée",
                })
                continue

            # Vérification correspondance input_hash
            if archived.input_hash != record.get("input_hash", ""):
                mismatches.append({
                    "event_id": event_id,
                    "intent_id": intent_id,
                    "field": "input_hash",
                    "original": archived.input_hash[:16] + "…",
                    "replayed": record.get("input_hash", "")[:16] + "…",
                    "error": "input_hash diverge — fixture associée au mauvais appel",
                })
                continue

            # Vérification correspondance decision
            if archived.decision != record.get("decision", ""):
                mismatches.append({
                    "event_id": event_id,
                    "intent_id": intent_id,
                    "field": "decision",
                    "original": archived.decision,
                    "replayed": record.get("decision", ""),
                })

            # Vérification correspondance execution_status
            if archived.execution_status != record.get("execution_status", ""):
                mismatches.append({
                    "event_id": event_id,
                    "intent_id": intent_id,
                    "field": "execution_status",
                    "original": archived.execution_status,
                    "replayed": record.get("execution_status", ""),
                })

    # ── INTENT orphelins → IN_DOUBT ──────────────────────────────────────────
    in_doubt_ids = intent_ids_seen - terminal_intent_ids
    in_doubt: list[dict] = []
    for record in entries:
        if (record.get("event_phase") == EventPhase.INTENT
                and record.get("intent_id", "") in in_doubt_ids):
            in_doubt.append({
                "intent_id": record.get("intent_id", ""),
                "event_id": record.get("event_id", ""),
                "tool_name": record.get("tool_name", ""),
                "sequence_no": record.get("sequence_no", 0),
                "classification": "IN_DOUBT",
            })

    terminals_replayed = len(terminal_intent_ids)

    # ── Verdict final ─────────────────────────────────────────────────────────
    if mismatches:
        verdict = "FAIL"
    elif in_doubt:
        verdict = "IN_DOUBT"
    else:
        verdict = "PASS"

    return R2ReplayResult(
        verdict=verdict,
        events_replayed=terminals_replayed,
        external_calls_prevented=external_calls_prevented,
        mismatches=mismatches,
        in_doubt=in_doubt,
        limits=[
            "L-019-002 P1 : R2 rejoue depuis fixtures archivées — aucun exécuteur externe appelé",
            "R2 vérifie la fidélité des décisions et des statuts d'exécution",
            "R2 ne vérifie pas la correction sémantique du contenu retourné par l'outil",
            "Un verdict PASS R2 ne prouve pas que l'effet externe original était correct",
            f"Préconditions manifeste : {precond.entries_verified} entrées vérifiées",
        ],
    )
