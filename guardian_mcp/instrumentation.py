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
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION

    def to_canonical_dict(self) -> dict[str, Any]:
        """Corps canonique JCS-compatible (clés triées récursivement).

        Le champ previous_event_hash est inclus dans le corps canonique (R023-002) :
        tout changement d'ordre ou suppression d'un événement modifie le hash
        de l'événement suivant dans la chaîne.
        """
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

        # Produire l'événement — R023-002 : inclure le hash du précédent
        self._seq += 1
        prev_hash = self._events[-1][1] if self._events else GENESIS_HASH
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
            previous_event_hash=prev_hash,
        )
        event_hash = event.compute_hash()
        # Toujours alimenter _events (pour prev_hash et introspection),
        # même quand un sink externe est utilisé.
        self._events.append((event, event_hash))
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
        """Nombre d'événements enregistrés dans cette session (hors sentinel de reprise)."""
        return sum(1 for e, _ in self._events if e is not None)

    def get_events(self) -> list[tuple[MCPToolEvent, str]]:
        """Retourne tous les événements (event, hash) de la session (hors sentinel de reprise)."""
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
            "event_id": event.event_id,
            "event_type": event.event_type,
            "occurred_at": event.occurred_at,
            "tool_name": event.tool_name,
            "agent_id": event.agent_id,
            "session_id": event.session_id,
            "run_id": event.run_id,
            "sequence_no": event.sequence_no,
            "decision": event.decision.value,
            "decision_reason": event.decision_reason,
            "input_hash": event.input_hash,
            "output_summary": event.output_summary,
            "duration_ms": event.duration_ms,
            "previous_event_hash": event.previous_event_hash,
            "schema_id": event.schema_id,
            "schema_version": event.schema_version,
            "event_hash": event_hash,
        }
        line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

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
        canonical_fields = {
            k: record[k]
            for k in (
                "agent_id", "decision", "decision_reason", "duration_ms",
                "event_id", "event_type", "input_hash", "occurred_at",
                "output_summary", "previous_event_hash", "run_id",
                "schema_id", "schema_version", "sequence_no",
                "session_id", "tool_name",
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
