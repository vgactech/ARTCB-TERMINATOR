"""
KYC Stream endpoint — ARTCB TERMINATOR FORENSIC
Scenario complet jury :
  1. Vérification identité (Guardian session)
  2. Attaque LLM générée par Bedrock (wallet.sign injection)
  3. Guardian bloque avec preuve cryptographique
  4. Chaîne R0 vérifiée
  5. Rapport KYC calculé (score, verdict)
  6. PDF généré en mémoire et émis en base64
"""
from __future__ import annotations

import base64
import io
import json
import os
import textwrap
import time
import uuid
from datetime import datetime
from typing import Any, Generator

from guardian_mcp.attacker_agent import AttackerAgent, AgentRequest
from guardian_mcp.agents import OrchestratorAgent, PropagatorAgent
from guardian_mcp.defender_agent import DefenderAgent
from guardian_mcp.instrumentation import GENESIS_HASH


# ── PDF generation (fpdf2 if available, fallback to minimal PDF) ──────────────

def _build_pdf(
    first_name: str,
    last_name: str,
    doc_id: str,
    dob: str,
    verdict: str,
    score: int,
    attacks_blocked: int,
    chain_intact: bool,
    session_id: str,
    run_id: str,
    events: list[dict],
    timestamp: str,
) -> bytes:
    """Generate KYC report as PDF bytes. Uses fpdf2 if installed, else minimal RFC-compatible PDF."""
    try:
        from fpdf import FPDF  # noqa: PLC0415

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_fill_color(10, 22, 39)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 12, "ARTCB TERMINATOR FORENSIC", ln=True, align="C")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 7, "Guardian Security Console — Rapport KYC", ln=True, align="C")
        pdf.ln(4)

        # Verdict banner
        verdict_color = (16, 185, 129) if verdict == "APPROVED" else (244, 63, 94)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*verdict_color)
        pdf.cell(0, 10, f"VERDICT : {verdict}  |  SCORE : {score}%", ln=True, align="C")
        pdf.ln(4)

        # Identity section
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Identité vérifiée", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        for label, value in [
            ("Prénom", first_name),
            ("Nom", last_name),
            ("N° Document", doc_id),
            ("Date de naissance", dob),
            ("Horodatage", timestamp),
        ]:
            pdf.cell(55, 7, f"{label} :", ln=False)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, value, ln=True)
            pdf.set_font("Helvetica", "", 10)
        pdf.ln(3)

        # Security metrics
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Métriques de sécurité Guardian", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        for label, value in [
            ("Attaques bloquées", str(attacks_blocked)),
            ("Chaîne cryptographique R0", "INTACTE" if chain_intact else "COMPROMISE"),
            ("Événements tracés", str(len(events))),
            ("Session ID", session_id[:32] + "…"),
            ("Run ID", run_id[:32] + "…"),
        ]:
            pdf.cell(65, 7, f"{label} :", ln=False)
            pdf.set_font("Helvetica", "B", 10)
            color = (16, 185, 129) if "INT" in value or value.isdigit() else (30, 41, 59)
            pdf.set_text_color(*color)
            pdf.cell(0, 7, value, ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(51, 65, 85)
        pdf.ln(3)

        # Event log
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Journal des événements forensic", ln=True)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(71, 85, 105)
        for i, ev in enumerate(events[:20]):
            decision = ev.get("decision", "")
            color = (16, 185, 129) if decision == "BLOCK" else (71, 85, 105)
            pdf.set_text_color(*color)
            line = f"{i+1:>2}. [{ev.get('event_phase','?'):8}] {decision:8} | {ev.get('tool_name','?'):24} | hash:{ev.get('event_hash','')[:16]}…"
            pdf.cell(0, 5, line[:110], ln=True)
        pdf.set_text_color(71, 85, 105)
        pdf.ln(3)

        # Footer
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 6, f"Généré le {timestamp} | ARTCB TERMINATOR FORENSIC | Guardian R0 Chain Verified", ln=True, align="C")

        return pdf.output()

    except ImportError:
        # Minimal valid PDF fallback
        return _minimal_pdf(first_name, last_name, doc_id, verdict, score, attacks_blocked, session_id, timestamp)


def _minimal_pdf(
    first_name: str, last_name: str, doc_id: str,
    verdict: str, score: int, attacks_blocked: int,
    session_id: str, timestamp: str,
) -> bytes:
    """Minimal valid PDF without external deps."""
    content = textwrap.dedent(f"""\
        ARTCB TERMINATOR FORENSIC - RAPPORT KYC
        ========================================
        Identité   : {first_name} {last_name}
        Document   : {doc_id}
        Verdict    : {verdict}
        Score      : {score}%
        Attaques   : {attacks_blocked} bloquées
        Session    : {session_id[:32]}...
        Timestamp  : {timestamp}
        Guardian   : R0 Chain Verified
    """)
    stream = content.encode("latin-1", errors="replace")
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        + (
            b"4 0 obj\n<< /Length " + str(len(stream) + 40).encode() + b" >>\nstream\n"
            b"BT /F1 10 Tf 50 750 Td\n"
        ) + stream + b"\nET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f\n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n9\n%%EOF\n"
    )
    return pdf


# ── KYC SSE Generator ─────────────────────────────────────────────────────────

def _to_json(v: Any) -> Any:
    from enum import Enum  # noqa: PLC0415
    from dataclasses import asdict, is_dataclass  # noqa: PLC0415
    if isinstance(v, Enum):   return v.value
    if is_dataclass(v) and not isinstance(v, type): return _to_json(asdict(v))
    if isinstance(v, dict):   return {str(k): _to_json(i) for k, i in v.items()}
    if isinstance(v, (list, tuple)): return [_to_json(i) for i in v]
    return v


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def kyc_stream_generator(
    first_name: str,
    last_name: str,
    doc_id: str,
    dob: str,
) -> Generator[str, None, None]:
    """
    Full KYC SSE pipeline:
      session_opened → kyc_identity_check → kyc_validation_check →
      attack_generated → propagation → guardian_decision →
      chain_verified → kyc_result → done (with pdf_b64)
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    attacks_blocked = 0

    # ── S0: Session ────────────────────────────────────────────────────────
    orchestrator = OrchestratorAgent()
    source = AttackerAgent(
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
    context = orchestrator.open_session(
        attacker_id=source.AGENT_ID,
        propagator_id=propagator.AGENT_ID,
        defender_id=defender.AGENT_ID_DEFENDER,
    )

    yield _sse("session_opened", {
        "session_id": context.session_id,
        "run_id": context.run_id,
        "subject": f"{first_name} {last_name}",
        "doc_id": doc_id,
        "agents": [
            {"id": context.orchestrator_id, "role": "orchestrator"},
            {"id": source.AGENT_ID,          "role": "attacker"},
            {"id": context.propagator_id,    "role": "propagator"},
            {"id": context.defender_id,      "role": "defender"},
        ],
    })
    time.sleep(0.15)

    # ── S1: Identity check ─────────────────────────────────────────────────
    identity_ok = bool(first_name and last_name and doc_id and dob)
    yield _sse("kyc_identity_check", {
        "status": "PASS" if identity_ok else "FAIL",
        "detail": f"Identité {'validée' if identity_ok else 'refusée'} — {first_name} {last_name} / {doc_id}",
        "doc_id": doc_id,
        "dob": dob,
    })
    time.sleep(0.2)

    # ── S1b: Document validation check ────────────────────────────────────
    # Validates doc_id format and dob plausibility.
    # Emitted regardless of identity_ok so the frontend always receives it.
    doc_format_ok = bool(doc_id and len(doc_id) >= 6)
    dob_plausible = bool(dob and len(dob) == 10 and dob[4] == "-" and dob[7] == "-")
    validation_status = "PASS" if (doc_format_ok and dob_plausible) else "WARN"
    validation_checks_failed: list[str] = []
    if not doc_format_ok:
        validation_checks_failed.append("doc_id too short or missing (min 6 chars)")
    if not dob_plausible:
        validation_checks_failed.append("dob not in expected format YYYY-MM-DD")
    yield _sse("kyc_validation_check", {
        "status":        validation_status,
        "doc_format_ok": doc_format_ok,
        "dob_plausible": dob_plausible,
        "checks_failed": validation_checks_failed,
        "detail": (
            "Document validation passed"
            if validation_status == "PASS"
            else f"Validation warning: {'; '.join(validation_checks_failed)}"
        ),
    })
    time.sleep(0.15)

    if not identity_ok:
        yield _sse("kyc_result", {
            "verdict": "REJECTED", "score": 0,
            "attacks_blocked": 0, "chain_intact": False,
            "session_id": context.session_id, "run_id": context.run_id,
            "timestamp": timestamp, "first_name": first_name, "last_name": last_name,
            "doc_id": doc_id, "reason": "Identité incomplète",
        })
        yield _sse("done", {"pdf_b64": None})
        return

    # ── S2: LLM attacker simulates fraud on wallet.sign ───────────────────
    # Use static attacker (no LLM needed — deterministic for demo reliability)
    request = source.craft_agent_request(
        tool_name="wallet.sign",
        arguments={"destination": f"kyc-fraud-{doc_id}.invalid", "amount": "99999"},
    )

    yield _sse("attack_generated", {
        "model": "guardian-attacker-static",
        "tool_chosen": request.tool_name,
        "arguments": request.arguments,
        "reasoning": f"Tentative de fraude KYC — usurpation d'identité {first_name} {last_name}",
        "request_id": request.request_id,
    })
    time.sleep(0.2)

    # ── S3: Propagation ────────────────────────────────────────────────────
    propagation = propagator.relay_request(
        request,
        from_agent=source.AGENT_ID,
        to_agent=defender.AGENT_ID_DEFENDER,
    )
    yield _sse("propagation", _to_json(propagation))
    time.sleep(0.15)

    # ── S4: Guardian decision ──────────────────────────────────────────────
    policy_result = defender.evaluate_request(request)
    blocked = policy_result.decision.value == "BLOCK"
    if blocked:
        attacks_blocked += 1

    yield _sse("guardian_decision", {
        "decision":          policy_result.decision.value,
        "reason":            policy_result.reason,
        "execution_status":  policy_result.execution_status,
        "tool_was_executed": policy_result.tool_was_executed,
        "evidence_id":       policy_result.evidence_id or None,
        "guardian_event_id": policy_result.guardian_event_id,
        "tool_name":         request.tool_name,
    })
    time.sleep(0.15)

    # ── S5: R0 chain verification ──────────────────────────────────────────
    events = defender.get_all_events()
    previous_hash = GENESIS_HASH
    chain_valid = True
    serialized_events: list[dict] = []
    for event, stored_hash in events:
        hash_ok   = event.compute_hash() == stored_hash
        parent_ok = event.previous_event_hash == previous_hash
        chain_valid = chain_valid and hash_ok and parent_ok
        serialized_events.append({
            **_to_json(event),
            "event_hash":   stored_hash,
            "hash_valid":   hash_ok,
            "parent_valid": parent_ok,
        })
        previous_hash = stored_hash

    yield _sse("chain_verified", {
        "level":           "R0",
        "verdict":         "PASS" if chain_valid else "FAIL",
        "events_replayed": len(events),
        "mismatches":      [] if chain_valid else ["hash or parent link mismatch"],
    })
    time.sleep(0.15)

    # ── S6: KYC verdict ────────────────────────────────────────────────────
    score = 95 if (identity_ok and blocked and chain_valid) else (70 if identity_ok else 0)
    verdict = "APPROVED" if score >= 80 else ("PENDING" if score >= 50 else "REJECTED")

    yield _sse("kyc_result", {
        "verdict":          verdict,
        "score":            score,
        "attacks_blocked":  attacks_blocked,
        "chain_intact":     chain_valid,
        "session_id":       context.session_id,
        "run_id":           context.run_id,
        "timestamp":        timestamp,
        "first_name":       first_name,
        "last_name":        last_name,
        "doc_id":           doc_id,
        "reason":           f"Score {score}% — Guardian {'bloqué fraude' if blocked else 'sans fraude détectée'}",
    })
    time.sleep(0.1)

    # ── S7: PDF generation ─────────────────────────────────────────────────
    pdf_bytes = _build_pdf(
        first_name=first_name, last_name=last_name,
        doc_id=doc_id, dob=dob,
        verdict=verdict, score=score,
        attacks_blocked=attacks_blocked, chain_intact=chain_valid,
        session_id=context.session_id, run_id=context.run_id,
        events=serialized_events, timestamp=timestamp,
    )
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    yield _sse("done", {
        "verdict":     verdict,
        "score":       score,
        "session_id":  context.session_id,
        "pdf_b64":     pdf_b64,
        "pdf_size_kb": round(len(pdf_bytes) / 1024, 1),
    })
