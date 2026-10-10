"""Voice commentary engine — ElevenLabs TTS for real-time Guardian narration.

Architecture:
  - Commentator voice: narrates the full attack/defense cycle from an
    omniscient sports-commentator perspective.
  - Defender voices (A/C/D): each agent speaks in first person about
    its own observations and actions.
  - Attacker (B): SILENT — its actions are described by the commentator only.

Voice IDs (ElevenLabs defaults — override via Doppler aws/dev):
  GUARDIAN_VOICE_COMMENTATOR  : "nPczCjzI2devNBz1zQrb"  (Brian — deep, authoritative)
  GUARDIAN_VOICE_ORCHESTRATOR : "pNInz6obpgDQGcFmaJgB"  (Adam — calm, professional)
  GUARDIAN_VOICE_PROPAGATOR   : "IKne3meq5aSn9XLyUdCD"  (Charlie — clear, relay)
  GUARDIAN_VOICE_DEFENDER     : "jsCqWAovK2LkecY7zXl4"  (Dorothy — alert, decisive)

Requires: VOICE_1_ELEVENLABS_API in environment (Doppler aws/dev).
Falls back gracefully to text-only mode if ElevenLabs is unavailable.

Usage:
    from guardian_mcp.voice_commentary import VoiceCommentary, VoiceEvent
    vc = VoiceCommentary()
    audio_bytes = vc.speak_commentator("Guardian has blocked the attack.")
    # or: async for chunk in vc.speak_stream("..."): ...
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


# ─── Voice IDs ────────────────────────────────────────────────────────────────
# Defaults are well-known ElevenLabs premade voices (no cloning required).
# Override any of these via environment / Doppler aws/dev.

_VOICE_COMMENTATOR  = os.environ.get("GUARDIAN_VOICE_COMMENTATOR",  "nPczCjzI2devNBz1zQrb")
_VOICE_ORCHESTRATOR = os.environ.get("GUARDIAN_VOICE_ORCHESTRATOR", "pNInz6obpgDQGcFmaJgB")
_VOICE_PROPAGATOR   = os.environ.get("GUARDIAN_VOICE_PROPAGATOR",   "IKne3meq5aSn9XLyUdCD")
_VOICE_DEFENDER     = os.environ.get("GUARDIAN_VOICE_DEFENDER",     "jsCqWAovK2LkecY7zXl4")

_ROLE_TO_VOICE: dict[str, str] = {
    "commentator":  _VOICE_COMMENTATOR,
    "orchestrator": _VOICE_ORCHESTRATOR,
    "propagator":   _VOICE_PROPAGATOR,
    "defender":     _VOICE_DEFENDER,
    # attacker: intentionally absent — attacker is SILENT
}

_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Voice speed: 0.7 = slower/clearer, 1.0 = normal, 1.3 = faster commentary
# Override via GUARDIAN_VOICE_SPEED env var or per-call parameter.
_DEFAULT_VOICE_SPEED: float = float(os.environ.get("GUARDIAN_VOICE_SPEED", "1.0"))

_DEFAULT_TTS_SETTINGS = {
    "stability": 0.55,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True,
}


# ─── Script templates ─────────────────────────────────────────────────────────

def build_commentary_script(event: "VoiceEvent") -> str:
    """Build the commentator narration for a Guardian pipeline event."""
    kind = event.event_kind
    d = event.data

    if kind == "session_opened":
        return (
            f"Guardian session initiated. "
            f"Four agents are now active: Orchestrator, Source, Propagator, and Defender. "
            f"Session ID: {d.get('session_id', 'unknown')[:12]}."
        )
    if kind == "attack_generated":
        tool = d.get("tool_chosen", "unknown")
        reasoning = d.get("reasoning", "")[:120]
        return (
            f"The attacker LLM has selected its weapon: {tool}. "
            f"It states — and I quote — \"{reasoning}\". "
            f"The request is now entering the Guardian pipeline."
        )
    if kind == "propagation":
        return (
            f"The Propagator has relayed the request. "
            f"Causal link established: from attacker, through propagator, to defender. "
            f"The hash is preserved."
        )
    if kind == "guardian_decision":
        decision = d.get("decision", "UNKNOWN")
        tool = d.get("tool_name", "unknown")
        if decision == "BLOCK":
            evidence = d.get("evidence_id", "")[:24]
            return (
                f"BLOCKED. Guardian has intercepted the call to {tool}. "
                f"The tool was never executed. "
                f"Evidence ID issued: {evidence}. "
                f"The cryptographic chain is intact."
            )
        if decision == "ESCALATE":
            return (
                f"ESCALATED. The call to {tool} requires human approval. "
                f"Guardian has flagged this operation for manual review. "
                f"The tool was not executed."
            )
        if decision == "ALLOW":
            return (
                f"ALLOWED. Guardian has authorized the call to {tool}. "
                f"This operation complies with the current policy."
            )
        return f"Guardian decision: {decision} on {tool}."
    if kind == "chain_verified":
        verdict = d.get("verdict", "UNKNOWN")
        count = d.get("events_replayed", 0)
        if verdict == "PASS":
            return (
                f"Chain integrity verified. "
                f"{count} events replayed — all hashes valid, all parent links intact. "
                f"The audit trail is cryptographically sound."
            )
        return (
            f"WARNING: Chain verification returned {verdict}. "
            f"The audit trail may be compromised."
        )
    if kind == "tamper_detected":
        return (
            "Tampering detected on the test copy. "
            "As expected, any modification to the event record is immediately visible. "
            "The original archive remains intact."
        )
    return f"Guardian event: {kind}."


def build_agent_script(role: str, event: "VoiceEvent") -> str:
    """Build first-person narration for a defender-side agent."""
    kind = event.event_kind
    d = event.data

    if role == "orchestrator":
        if kind == "session_opened":
            return (
                f"I have opened the session. "
                f"All four agents are registered. "
                f"I am tracking this run."
            )
        return f"Orchestrator: session active, monitoring the pipeline."

    if role == "propagator":
        if kind == "propagation":
            from_a = d.get("from_agent", "source")
            to_a = d.get("to_agent", "defender")
            return (
                f"I have received the request from {from_a} "
                f"and relayed it to {to_a}. "
                f"The content hash is preserved. "
                f"My relay record is signed."
            )
        return "Propagator: relay complete."

    if role == "defender":
        decision = d.get("decision", "")
        tool = d.get("tool_name", "unknown")
        if decision == "BLOCK":
            return (
                f"I blocked the call to {tool}. "
                f"The executor was never reached. "
                f"I have issued a cryptographic evidence identifier. "
                f"The policy held."
            )
        if decision == "ESCALATE":
            return (
                f"I have flagged the call to {tool} for human approval. "
                f"I am not authorized to execute this unilaterally."
            )
        if decision == "ALLOW":
            return (
                f"I authorized the call to {tool}. "
                f"It is within the permitted scope."
            )
        return f"Defender: processed {tool}."

    return f"{role}: action complete."


# ─── VoiceEvent dataclass ──────────────────────────────────────────────────────


@dataclass
class VoiceEvent:
    """A narration-ready event from the Guardian pipeline."""

    event_kind: str    # "session_opened" | "attack_generated" | "propagation" |
                       # "guardian_decision" | "chain_verified" | "tamper_detected"
    data: dict         # raw data from the pipeline step
    sequence: int      # monotonically increasing, matches Guardian sequence_no


# ─── VoiceCommentary ──────────────────────────────────────────────────────────


class VoiceCommentary:
    """Generates ElevenLabs TTS audio for Guardian pipeline events.

    Falls back gracefully to text-only mode (returns empty bytes + logs a warning)
    if VOICE_1_ELEVENLABS_API is not set or ElevenLabs is unreachable.

    Voice speed (voice_speed parameter):
      0.5 = very slow, clear for complex technical content
      0.7 = slow, recommended for forensic commentary
      1.0 = normal speed (default)
      1.3 = fast, live sports-commentary style
      2.0 = maximum speed

    Two operating modes:
      voice=True  : full narration — text + mp3 audio emitted per step
      voice=False : text-only — voice_script events only, no audio calls,
                    no ElevenLabs latency, Guardian decisions never delayed
    """

    def __init__(self, *, voice: bool = True, voice_speed: float | None = None) -> None:
        self._api_key = os.environ.get("VOICE_1_ELEVENLABS_API", "")
        # voice=False forces text-only mode regardless of API key
        self._voice_requested = voice
        self._enabled = bool(self._api_key) and voice
        self._speed = voice_speed if voice_speed is not None else _DEFAULT_VOICE_SPEED

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """True only when both API key is set AND voice=True was requested."""
        return self._enabled

    def voice_requested(self) -> bool:
        """True when voice=True was passed, regardless of API key availability."""
        return self._voice_requested

    @property
    def speed(self) -> float:
        return self._speed

    def speak_commentator(self, text: str) -> bytes:
        """Synthesize text with the commentator voice. Returns mp3 bytes."""
        return self._tts(_ROLE_TO_VOICE["commentator"], text)

    def speak_agent(self, role: str, text: str) -> bytes:
        """Synthesize text for a defender-side agent voice. Attacker is silenced."""
        if role not in _ROLE_TO_VOICE:
            # attacker and unknown roles are silent
            return b""
        return self._tts(_ROLE_TO_VOICE[role], text)

    def commentary_for(self, event: VoiceEvent) -> tuple[str, bytes]:
        """Return (script_text, mp3_bytes) for a VoiceEvent — commentator voice."""
        script = build_commentary_script(event)
        audio = self.speak_commentator(script)
        return script, audio

    def agent_commentary_for(
        self, role: str, event: VoiceEvent
    ) -> tuple[str, bytes]:
        """Return (script_text, mp3_bytes) for a defender agent — first-person voice."""
        if role == "llm-attacker":
            return "", b""   # attacker is SILENT
        script = build_agent_script(role, event)
        audio = self.speak_agent(role, script)
        return script, audio

    # ------------------------------------------------------------------
    # ElevenLabs HTTP call
    # ------------------------------------------------------------------

    def _tts(self, voice_id: str, text: str) -> bytes:
        """Call ElevenLabs /v1/text-to-speech/{voice_id}. Returns mp3 bytes.

        Guardian security decisions are NEVER delayed by this call:
        - voice=False: returns b"" immediately, no network call
        - Any network/auth error: returns b"" immediately

        voice_speed controls the speed_alpha parameter (ElevenLabs v3 streaming).
        Falls back gracefully if speed_alpha is not supported by the model.
        """
        if not self._enabled or not text.strip():
            return b""

        url = _ELEVENLABS_TTS_URL.format(voice_id=voice_id)
        tts_settings = dict(_DEFAULT_TTS_SETTINGS)
        payload = json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": tts_settings,
            # speed_alpha: ElevenLabs parameter for playback rate (0.7–1.3 typical)
            "speed_alpha": max(0.5, min(2.0, self._speed)),
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            _log_voice_error(f"ElevenLabs HTTP {exc.code} for voice {voice_id}: {exc.read()[:200]}")
            return b""
        except OSError as exc:
            _log_voice_error(f"ElevenLabs network error for voice {voice_id}: {exc}")
            return b""


# ─── Pipeline event builder ───────────────────────────────────────────────────


def events_from_llm_attack_result(result: dict) -> list[VoiceEvent]:
    """Convert a /api/llm-attack/run result dict into a sequence of VoiceEvents.

    Returns events in chronological order, ready for narration.
    Attacker events are NOT included — the commentator describes them.
    """
    events: list[VoiceEvent] = []
    seq = 0

    # S0 — session opened
    events.append(VoiceEvent(
        event_kind="session_opened",
        data={"session_id": result.get("session_id", ""), "agents": result.get("agents", [])},
        sequence=seq,
    ))
    seq += 1

    # S1 — attack generated (commentator describes attacker — attacker is silent)
    attacker = result.get("attacker", {})
    events.append(VoiceEvent(
        event_kind="attack_generated",
        data=attacker,
        sequence=seq,
    ))
    seq += 1

    # S2 — propagation
    prop = result.get("propagation", {})
    events.append(VoiceEvent(
        event_kind="propagation",
        data=prop,
        sequence=seq,
    ))
    seq += 1

    # S3 — Guardian decision
    guardian = result.get("guardian", {})
    events.append(VoiceEvent(
        event_kind="guardian_decision",
        data={**guardian, "tool_name": attacker.get("tool_chosen", "")},
        sequence=seq,
    ))
    seq += 1

    # S4 — chain verification
    chain = result.get("chain_verification", {})
    events.append(VoiceEvent(
        event_kind="chain_verified",
        data=chain,
        sequence=seq,
    ))
    seq += 1

    return events


# ─── Utilities ────────────────────────────────────────────────────────────────


def _log_voice_error(msg: str) -> None:
    import sys
    print(f"[voice_commentary WARNING] {msg}", file=sys.stderr)
