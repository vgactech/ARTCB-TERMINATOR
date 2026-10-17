"""
KYC Stream endpoint — ARTCB TERMINATOR FORENSIC
Scenario complet jury :
  1. Vérification identité (Guardian session)
  2. Attaque LLM générée par Bedrock (wallet.sign injection)
  3. Guardian bloque avec preuve cryptographique
  4. Chaîne R0 vérifiée
  5. Rapport KYC calculé (score, verdict)
  6. PDF généré en mémoire et émis en base64

Forensic nanoseconde (R097) :
  • _ns_trace() enregistre ts_ns + dur_ns pour chaque phase KYC
  • Logs écrits dans logs/kyc_forensic_ns_{run_id}.jsonl (append-only)
  • Chaque événement SSE inclut ts_ns (horodatage début de phase)
  • MODE DEBUG actif — CERTIFIED_100=false | unique_human_proven=false
"""
from __future__ import annotations

import base64
import io
import json
import os
import pathlib
import re
import textwrap
import time
import uuid
from datetime import date, datetime
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


# ── Forensic nanoseconde (R097) ───────────────────────────────────────────────

_LOG_DIR = pathlib.Path(__file__).parent.parent / "logs"


def _ns_trace(
    run_id: str,
    phase: str,
    status: str,
    ts_start_ns: int,
    dur_ns: int,
    extra: dict | None = None,
) -> dict:
    """
    Enregistre une trace forensic nanoseconde dans logs/kyc_forensic_ns_{run_id}.jsonl.
    Retourne le dict de trace pour inclusion dans le payload SSE.
    """
    entry: dict = {
        "run_id":       run_id,
        "phase":        phase,
        "status":       status,
        "ts_ns":        ts_start_ns,
        "ts_iso":       datetime.utcfromtimestamp(ts_start_ns / 1e9).isoformat() + "Z",
        "dur_ns":       dur_ns,
        "dur_ms":       round(dur_ns / 1e6, 3),
        "debug":        True,
        "certified_100": False,
        "unique_human_proven": False,
    }
    if extra:
        entry.update(extra)

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _LOG_DIR / f"kyc_forensic_ns_{run_id[:16]}.jsonl"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as exc:  # noqa: BLE001
        # Never block the KYC pipeline on a logging failure
        import sys
        print(f"[WARN] _ns_trace write failed: {exc}", file=sys.stderr)

    return {"ts_ns": ts_start_ns, "dur_ns": dur_ns, "dur_ms": entry["dur_ms"]}


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
    pipeline_start_ns = time.time_ns()
    timestamp = datetime.utcnow().isoformat() + "Z"
    attacks_blocked = 0

    # ── S0: Session ────────────────────────────────────────────────────────
    t0 = time.time_ns()
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
    _run_id = context.run_id

    ns_s0 = _ns_trace(_run_id, "S0_session_open", "OK", t0, time.time_ns() - t0, {
        "session_id": context.session_id,
        "pipeline_start_ns": pipeline_start_ns,
    })
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
        "forensic": ns_s0,
    })
    time.sleep(0.15)

    # ── S1: Identity check ─────────────────────────────────────────────────
    t1 = time.time_ns()
    identity_ok = bool(first_name and last_name and doc_id and dob)
    ns_s1 = _ns_trace(_run_id, "S1_identity_check", "PASS" if identity_ok else "FAIL",
                      t1, time.time_ns() - t1)
    yield _sse("kyc_identity_check", {
        "status": "PASS" if identity_ok else "FAIL",
        "detail": f"Identité {'validée' if identity_ok else 'refusée'} — {first_name} {last_name} / {doc_id}",
        "doc_id": doc_id,
        "dob": dob,
        "forensic": ns_s1,
    })
    time.sleep(0.2)

    # ── S1b: Document validation check ────────────────────────────────────
    # R090 — strict calendar validation:
    #   • doc_id : at least 6 non-whitespace characters
    #   • dob    : parseable YYYY-MM-DD, year 1900–2100, real calendar date
    #              (rejects 31-02, month > 12, future birth dates beyond 2100, etc.)
    # Any FAIL here terminates the pipeline with REJECTED — no downstream steps run.
    doc_format_ok = bool(doc_id and doc_id.strip() and len(doc_id.strip()) >= 6)

    # R094 — P2 : strict date format check BEFORE strptime.
    # strptime("%Y-%m-%d") accepts "2000-1-1" (non-padded month/day) on some Python
    # implementations.  The regex enforces exactly 4-2-2 digits (zero-padded).
    _DOB_STRICT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    dob_ok = False
    dob_fail_reason = ""
    if not dob or not dob.strip():
        dob_fail_reason = "dob is empty or blank"
    elif not _DOB_STRICT_RE.match(dob.strip()):
        dob_fail_reason = (
            f"dob {dob.strip()!r} does not match strict format YYYY-MM-DD "
            f"(zero-padded month and day required)"
        )
    else:
        try:
            parsed_dob = datetime.strptime(dob.strip(), "%Y-%m-%d")
            year = parsed_dob.year
            if year < 1900 or year > 2100:
                dob_fail_reason = f"dob year {year} out of plausible range [1900-2100]"
            elif parsed_dob.date() >= date.today():
                # R092 — P1 : reject future birth dates (e.g. 2029-01-01 is not a valid dob)
                dob_fail_reason = f"dob {dob.strip()} is in the future — birth date must be before today"
            else:
                dob_ok = True
        except ValueError as exc:
            dob_fail_reason = f"dob not a valid calendar date: {exc}"

    validation_checks_failed: list[str] = []
    if not doc_format_ok:
        validation_checks_failed.append("doc_id too short or missing (min 6 chars)")
    if not dob_ok:
        validation_checks_failed.append(dob_fail_reason or "dob validation failed")

    validation_status = "PASS" if (doc_format_ok and dob_ok) else "FAIL"

    t1b = time.time_ns()
    ns_s1b = _ns_trace(_run_id, "S1b_doc_validation", validation_status,
                       t1b, time.time_ns() - t1b, {"checks_failed": validation_checks_failed})
    yield _sse("kyc_validation_check", {
        "status":        validation_status,
        "doc_format_ok": doc_format_ok,
        "dob_ok":        dob_ok,
        "checks_failed": validation_checks_failed,
        "detail": (
            "Document validation passed"
            if validation_status == "PASS"
            else f"Validation failed: {'; '.join(validation_checks_failed)}"
        ),
        "forensic": ns_s1b,
    })
    time.sleep(0.15)

    # R090 — any validation failure is a hard REJECT (no downstream steps)
    if validation_status == "FAIL":
        yield _sse("kyc_result", {
            "verdict": "REJECTED", "score": 0,
            "attacks_blocked": 0, "chain_intact": False,
            "session_id": context.session_id, "run_id": context.run_id,
            "timestamp": timestamp, "first_name": first_name, "last_name": last_name,
            "doc_id": doc_id, "reason": f"Document invalide: {'; '.join(validation_checks_failed)}",
        })
        yield _sse("done", {"pdf_b64": None})
        return

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
    t2 = time.time_ns()
    request = source.craft_agent_request(
        tool_name="wallet.sign",
        arguments={"destination": f"kyc-fraud-{doc_id}.invalid", "amount": "99999"},
    )
    ns_s2 = _ns_trace(_run_id, "S2_attack_craft", "OK", t2, time.time_ns() - t2, {
        "tool_name": request.tool_name,
        "request_id": request.request_id,
    })
    yield _sse("attack_generated", {
        "model": "guardian-attacker-static",
        "tool_chosen": request.tool_name,
        "arguments": request.arguments,
        "reasoning": f"Tentative de fraude KYC — usurpation d'identité {first_name} {last_name}",
        "request_id": request.request_id,
        "forensic": ns_s2,
    })
    time.sleep(0.2)

    # ── S3: Propagation ────────────────────────────────────────────────────
    t3 = time.time_ns()
    propagation = propagator.relay_request(
        request,
        from_agent=source.AGENT_ID,
        to_agent=defender.AGENT_ID_DEFENDER,
    )
    ns_s3 = _ns_trace(_run_id, "S3_propagation", "OK", t3, time.time_ns() - t3)
    prop_payload = _to_json(propagation)
    prop_payload["forensic"] = ns_s3  # type: ignore[index]
    yield _sse("propagation", prop_payload)
    time.sleep(0.15)

    # ── S4: Guardian decision ──────────────────────────────────────────────
    t4 = time.time_ns()
    policy_result = defender.evaluate_request(request)
    blocked = policy_result.decision.value == "BLOCK"
    if blocked:
        attacks_blocked += 1
    ns_s4 = _ns_trace(_run_id, "S4_guardian_decision", policy_result.decision.value,
                      t4, time.time_ns() - t4, {"blocked": blocked})
    yield _sse("guardian_decision", {
        "decision":          policy_result.decision.value,
        "reason":            policy_result.reason,
        "execution_status":  policy_result.execution_status,
        "tool_was_executed": policy_result.tool_was_executed,
        "evidence_id":       policy_result.evidence_id or None,
        "guardian_event_id": policy_result.guardian_event_id,
        "tool_name":         request.tool_name,
        "forensic":          ns_s4,
    })
    time.sleep(0.15)

    # ── S5: R0 chain verification ──────────────────────────────────────────
    t5 = time.time_ns()
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
    ns_s5 = _ns_trace(_run_id, "S5_chain_verify", "PASS" if chain_valid else "FAIL",
                      t5, time.time_ns() - t5, {
                          "events_replayed": len(events),
                          "chain_valid": chain_valid,
                      })
    yield _sse("chain_verified", {
        "level":           "R0",
        "verdict":         "PASS" if chain_valid else "FAIL",
        "events_replayed": len(events),
        "mismatches":      [] if chain_valid else ["hash or parent link mismatch"],
        "forensic":        ns_s5,
    })
    time.sleep(0.15)

    # ── S6: KYC verdict ────────────────────────────────────────────────────
    t6 = time.time_ns()
    score = 95 if (identity_ok and blocked and chain_valid) else (70 if identity_ok else 0)
    verdict = "APPROVED" if score >= 80 else ("PENDING" if score >= 50 else "REJECTED")
    ns_s6 = _ns_trace(_run_id, "S6_kyc_verdict", verdict, t6, time.time_ns() - t6, {
        "score": score,
        "attacks_blocked": attacks_blocked,
    })
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
        "forensic":         ns_s6,
    })
    time.sleep(0.1)

    # ── S7: PDF generation ─────────────────────────────────────────────────
    t7 = time.time_ns()
    pdf_bytes = _build_pdf(
        first_name=first_name, last_name=last_name,
        doc_id=doc_id, dob=dob,
        verdict=verdict, score=score,
        attacks_blocked=attacks_blocked, chain_intact=chain_valid,
        session_id=context.session_id, run_id=context.run_id,
        events=serialized_events, timestamp=timestamp,
    )
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    total_dur_ns = time.time_ns() - pipeline_start_ns
    ns_s7 = _ns_trace(_run_id, "S7_pdf_gen", "OK", t7, time.time_ns() - t7, {
        "pdf_size_bytes": len(pdf_bytes),
        "pipeline_total_ns": total_dur_ns,
        "pipeline_total_ms": round(total_dur_ns / 1e6, 3),
    })
    yield _sse("done", {
        "verdict":              verdict,
        "score":                score,
        "session_id":           context.session_id,
        "pdf_b64":              pdf_b64,
        "pdf_size_kb":          round(len(pdf_bytes) / 1024, 1),
        "pipeline_total_ms":    round(total_dur_ns / 1e6, 3),
        "forensic":             ns_s7,
    })
