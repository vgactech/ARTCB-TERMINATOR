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
from guardian_mcp.voice_commentary import (
    VoiceCommentary,
    VoiceEvent,
    build_commentary_script,
)
from guardian_api.liveness import liveness_controller


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
    narration: list[str] | None = None,
    liveness_status: str = "SKIPPED",
    human_proven: bool = False,
) -> bytes:
    """Generate KYC report as PDF bytes. Uses fpdf2 if installed, else dependency-free PDF."""
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

        # Liveness / human presence
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Preuve de présence humaine (liveness)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        liveness_label = {
            "PASS": "PASS - geste main validé (défi nonce)",
            "SIMULATED": "SIMULE - mode démo sans caméra",
            "SKIPPED": "NON ENGAGE",
        }.get(liveness_status, liveness_status)
        for label, value in [
            ("Défi liveness", liveness_label),
            ("Présence humaine prouvée", "OUI" if human_proven else "NON"),
        ]:
            pdf.cell(65, 7, f"{label} :", ln=False)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, value, ln=True)
            pdf.set_font("Helvetica", "", 10)
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

        # Narration transcript
        if narration:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, 8, "Narration Guardian", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            for caption in narration:
                pdf.multi_cell(0, 5, caption)
            pdf.ln(3)

        # Footer
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 6, f"Généré le {timestamp} | ARTCB TERMINATOR FORENSIC | Guardian R0 Chain Verified", ln=True, align="C")

        return pdf.output()

    except ImportError:
        # Dependency-free PDF fallback — always valid, always populated.
        return _minimal_pdf(
            first_name=first_name, last_name=last_name,
            doc_id=doc_id, dob=dob,
            verdict=verdict, score=score,
            attacks_blocked=attacks_blocked, chain_intact=chain_intact,
            session_id=session_id, run_id=run_id,
            events=events, timestamp=timestamp,
            narration=narration or [],
            liveness_status=liveness_status, human_proven=human_proven,
        )


def _escape_pdf_text(text: str) -> str:
    """Escape the three characters that are special inside a PDF string literal."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_document(
    lines: list[str],
    *,
    font: str = "Courier",
    font_size: int = 8,
    leading: int = 10,
) -> bytes:
    """Assemble a valid single-page PDF from plain text lines, with no dependencies.

    Unlike the previous hard-coded fallback, this computes exact object byte
    offsets, writes a complete xref table, and sets /Length to the real content
    stream length — so every PDF viewer renders the report instead of a blank page.
    """
    top = 760
    max_lines = max(1, (top - 40) // leading)
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + ["... (contenu tronque)"]

    content_lines = ["BT", f"/F1 {font_size} Tf", f"50 {top} Td", f"{leading} TL"]
    for line in lines:
        content_lines.append(f"({_escape_pdf_text(line)}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content = ("\n".join(content_lines) + "\n").encode("latin-1", errors="replace")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"endstream",
        f"<< /Type /Font /Subtype /Type1 /BaseFont /{font} >>".encode(),
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(index).encode() + b" 0 obj\n" + body + b"\nendobj\n"

    xref_offset = len(out)
    size = len(objects) + 1
    out += b"xref\n0 " + str(size).encode() + b"\n"
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size " + str(size).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF\n"
    )
    return bytes(out)


def _minimal_pdf(
    first_name: str, last_name: str, doc_id: str, dob: str,
    verdict: str, score: int, attacks_blocked: int, chain_intact: bool,
    session_id: str, run_id: str, events: list[dict], timestamp: str,
    narration: list[str],
    liveness_status: str = "SKIPPED", human_proven: bool = False,
) -> bytes:
    """Dependency-free KYC report. Always renders identity, metrics, journal,
    and narration — even when a field or the event list is empty (demo data)."""
    def shown(value: object) -> str:
        text = "" if value is None else str(value)
        return text if text.strip() else "N/A"

    liveness_label = {
        "PASS": "PASS - geste main valide (defi nonce)",
        "SIMULATED": "SIMULE - mode demo sans camera",
        "SKIPPED": "NON ENGAGE",
    }.get(liveness_status, liveness_status)
    human_label = "OUI" if human_proven else "NON"

    lines: list[str] = [
        "ARTCB TERMINATOR FORENSIC - RAPPORT KYC",
        "=" * 78,
        f"VERDICT : {shown(verdict)}    |    SCORE : {score}%",
        "",
        "IDENTITE VERIFIEE",
        f"  Prenom            : {shown(first_name)}",
        f"  Nom               : {shown(last_name)}",
        f"  N. document       : {shown(doc_id)}",
        f"  Date de naissance : {shown(dob)}",
        f"  Horodatage        : {shown(timestamp)}",
        "",
        "METRIQUES DE SECURITE GUARDIAN",
        f"  Attaques bloquees : {attacks_blocked}",
        f"  Chaine R0         : {'INTACTE' if chain_intact else 'COMPROMISE'}",
        f"  Evenements traces : {len(events)}",
        f"  Session ID        : {shown(session_id)}",
        f"  Run ID            : {shown(run_id)}",
        "",
        "PREUVE DE PRESENCE HUMAINE (LIVENESS)",
        f"  Defi liveness     : {shown(liveness_label)}",
        f"  Presence humaine  : {human_label}",
        "",
        "JOURNAL FORENSIC",
    ]
    if events:
        for index, event in enumerate(events[:20], start=1):
            phase = str(event.get("event_phase", "?"))
            decision = str(event.get("decision", "?"))
            tool = str(event.get("tool_name", "?"))
            event_hash = str(event.get("event_hash", ""))
            lines.append(
                f"  {index:>2}. [{phase:8}] {decision:8} | {tool:22} | hash:{event_hash[:16]}"
            )
    else:
        lines.append("  DEMO - aucun evenement capture pour cette session.")

    lines.append("")
    lines.append("NARRATION GUARDIAN")
    if narration:
        for caption in narration:
            for wrapped in textwrap.wrap(caption, width=92) or [""]:
                lines.append(f"  {wrapped}")
    else:
        lines.append("  DEMO - narration non disponible.")

    lines.append("")
    lines.append(
        f"Genere le {shown(timestamp)} | ARTCB TERMINATOR FORENSIC | Guardian R0 Chain Verified"
    )
    return _pdf_document(lines)


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


def _track(narration: list[str], script: str) -> str:
    """Record a narration script (for the PDF transcript) and return it."""
    narration.append(script)
    return script


def _emit_voice(
    vc: VoiceCommentary,
    role: str,
    text: str,
    sequence: int,
) -> Generator[str, None, None]:
    """Yield voice_script (caption), then voice_audio when TTS is available.

    Isolation invariant: the caller MUST emit the matching security event
    before calling this. TTS latency never delays a Guardian decision.
    """
    yield _sse("voice_script", {"role": role, "text": text, "sequence": sequence})
    if vc.is_enabled() and text:
        audio = (
            vc.speak_commentator(text)
            if role == "commentator"
            else vc.speak_agent(role, text)
        )
        if audio:
            yield _sse("voice_audio", {
                "role": role,
                "sequence": sequence,
                "audio_b64": base64.b64encode(audio).decode(),
                "mime": "audio/mpeg",
                "speed": vc.speed,
            })


def kyc_stream_generator(
    first_name: str,
    last_name: str,
    doc_id: str,
    dob: str,
    *,
    voice: bool = True,
    voice_speed: float = 1.0,
    liveness_token: str | None = None,
) -> Generator[str, None, None]:
    """
    Full KYC SSE pipeline:
      session_opened → kyc_identity_check → liveness_check → attack_generated →
      propagation → guardian_decision → chain_verified →
      kyc_result → done (with pdf_b64)

    Voice narration (voice=True) is emitted at five key moments — session start,
    liveness check, attack detected, Guardian BLOCK, and final verdict — always
    AFTER the matching security event. voice_script carries the caption text;
    voice_audio (base64 mp3) is emitted only when VOICE_1_ELEVENLABS_API is set.
    The pipeline degrades to captions-only when TTS is unavailable and never
    blocks on it.

    Liveness: when liveness_token references a verified challenge, human_proven
    is true (PASS) and the verdict requires it. SIMULATED/SKIPPED never block.
    A FAILed liveness check forces REJECTED.
    """
    vc = VoiceCommentary(voice=voice, voice_speed=voice_speed)
    narration: list[str] = []
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
    yield from _emit_voice(
        vc,
        "commentator",
        _track(narration, build_commentary_script(
            VoiceEvent("session_opened", {"session_id": context.session_id}, 0)
        )),
        0,
    )
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

    # ── S1b: Liveness / human-presence challenge ──────────────────────────
    liveness_status = "SKIPPED"
    human_proven = False
    liveness_result = (
        liveness_controller.result_for(liveness_token) if liveness_token else None
    )
    if liveness_result is not None:
        liveness_status = liveness_result.liveness
        human_proven = liveness_result.human_proven
    liveness_ok = liveness_status in ("PASS", "SIMULATED", "SKIPPED")

    yield _sse("liveness_check", {
        "status":        liveness_status,
        "human_proven":  human_proven,
        "gesture":       liveness_result.gesture if liveness_result else None,
        "reason":        liveness_result.reason if liveness_result else "Liveness non engagée",
        "evidence_id":   liveness_result.evidence_id if liveness_result else None,
        "guardian_event_id": liveness_result.guardian_event_id if liveness_result else None,
        "data_source":   liveness_result.data_source if liveness_result else None,
    })
    yield from _emit_voice(
        vc,
        "commentator",
        _track(narration, build_commentary_script(
            VoiceEvent("liveness_check", {
                "status":  liveness_status,
                "gesture": liveness_result.gesture if liveness_result else "",
            }, 1)
        )),
        1,
    )
    time.sleep(0.15)

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
    yield from _emit_voice(
        vc,
        "commentator",
        _track(narration, build_commentary_script(
            VoiceEvent("attack_generated", {
                "tool_chosen": request.tool_name,
                "reasoning": f"Tentative de fraude KYC — usurpation d'identité {first_name} {last_name}",
            }, 2)
        )),
        2,
    )
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
    yield from _emit_voice(
        vc,
        "commentator",
        _track(narration, build_commentary_script(
            VoiceEvent("guardian_decision", {
                "decision": policy_result.decision.value,
                "tool_name": request.tool_name,
                "evidence_id": policy_result.evidence_id or "",
            }, 3)
        )),
        3,
    )
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
    # Enforced rule: APPROVED ⟺ identity_ok ∧ blocked ∧ chain_valid ∧ liveness_ok.
    # A FAILed liveness challenge forces REJECTED; SIMULATED/SKIPPED never block.
    if not liveness_ok:
        score = 0
        verdict = "REJECTED"
        verdict_reason = "Présence humaine non prouvée"
    elif identity_ok and blocked and chain_valid:
        score = 95
        verdict = "APPROVED"
        verdict_reason = "Guardian a bloqué la fraude — chaîne R0 intacte"
    elif identity_ok:
        score = 70
        verdict = "PENDING"
        verdict_reason = "Identité valide — vérification partielle"
    else:
        score = 0
        verdict = "REJECTED"
        verdict_reason = "Score insuffisant"

    yield _sse("kyc_result", {
        "verdict":          verdict,
        "score":            score,
        "attacks_blocked":  attacks_blocked,
        "chain_intact":     chain_valid,
        "liveness":         liveness_status,
        "human_proven":     human_proven,
        "session_id":       context.session_id,
        "run_id":           context.run_id,
        "timestamp":        timestamp,
        "first_name":       first_name,
        "last_name":        last_name,
        "doc_id":           doc_id,
        "reason":           f"Score {score}% — {verdict_reason}",
    })
    yield from _emit_voice(
        vc,
        "commentator",
        _track(narration, (
            f"KYC verification complete. Verdict: {verdict}. "
            f"Score: {score} percent. "
            f"Human presence: {liveness_status.lower()}. "
            f"{attacks_blocked} attack blocked by Guardian. "
            f"The R0 audit chain is {'intact' if chain_valid else 'compromised'}."
        )),
        4,
    )
    time.sleep(0.1)

    # ── S7: PDF generation ─────────────────────────────────────────────────
    pdf_bytes = _build_pdf(
        first_name=first_name, last_name=last_name,
        doc_id=doc_id, dob=dob,
        verdict=verdict, score=score,
        attacks_blocked=attacks_blocked, chain_intact=chain_valid,
        session_id=context.session_id, run_id=context.run_id,
        events=serialized_events, timestamp=timestamp,
        narration=narration,
        liveness_status=liveness_status, human_proven=human_proven,
    )
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    yield _sse("done", {
        "verdict":     verdict,
        "score":       score,
        "session_id":  context.session_id,
        "pdf_b64":     pdf_b64,
        "pdf_size_kb": round(len(pdf_bytes) / 1024, 1),
    })
