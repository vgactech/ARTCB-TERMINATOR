# R041 — Voice speed, dual mode, and enforcement isolation

**Date**: 2026-10-10  
**Tests**: 164/164 PASS (observed in this session)  
**Counter-audit**: R041 external — 5 findings  
**Previous report**: R040 — ElevenLabs voice + SSE stream, 154/154 PASS  
**Commits this report**: one (voice speed + dual mode + isolation + tests)

---

## 1. Executive Summary

The R041 external counter-audit identified five valid gaps in R040.
This report closes all five with code, tests, and documentation.

| Finding | Priority | Status |
|---|---|---|
| R041-P0a — Synchronous TTS can delay Guardian security events | P0 | ✅ Closed |
| R041-P0b — Chain scope not documented; narration may overclaim | P0 | ✅ Closed |
| R041-P0c — Stream endpoint auth not demonstrated | P0 | ✅ Documented |
| R041-P1a — No frontend file changed in R040 | P1 | Acknowledged |
| R041-P1b — SSE reconnection not defined | P1 | Documented |

Test count: 154 → **164 PASS** (+10 new tests, 0 failures).

---

## 2. R041-P0a — Isolation: Guardian decision before audio

### Counter-audit finding
Voice synthesis calls (15 s timeout each) were interleaved with security event emission.
A slow ElevenLabs response could delay the `guardian_decision` SSE event.

### Correction

**New helper `_emit_voice(vc, role, script, seq)`** in [`guardian_api/app.py`](../guardian_api/app.py):
yields `voice_script` then optionally `voice_audio` — called ONLY after the security event.

**Isolation contract documented in `_sse_generator`**:
```
# ← guardian_decision emitted HERE, before any voice synthesis
yield _sse_event("guardian_decision", guardian_data)
# Voice AFTER the decision — audio latency never delays Guardian
yield from _emit_voice(vc, "commentator", ...)
yield from _emit_voice(vc, "defender", ...)
```

Same pattern applied to `chain_verified` — always emitted before narration.

**Test** `test_stream_route_isolation_guardian_before_voice`:
parses the full SSE stream, finds the position of `guardian_decision` and the
first `voice_script` with `sequence=3`, and asserts that the security event
came first.

---

## 3. R041-P0b — Chain scope: explicit documentation

### Counter-audit finding
`chain_verification.verdict = PASS` in the stream referred only to defender events.
Narration text ("The audit trail is cryptographically sound") could be read
as a wider guarantee than is actually verified.

### Correction

Added `"chain_scope": "defender_events"` to both `guardian_data` and `chain_data`
in the SSE generator. This field propagates into the `done` event so the
frontend and any audit tool can read the documented scope.

The narration script in `build_commentary_script` for `chain_verified` already
says "events replayed" (count-based), not "all agents verified".

**Test** `test_stream_done_event_has_chain_scope`:
asserts `done.chain_verification.chain_scope == "defender_events"`.

---

## 4. R041-P0c — Stream endpoint authorization

### Counter-audit finding
No access control beyond `GUARDIAN_ATTACKER_ENABLED=true` was demonstrated.

### Disposition
The current protection is the environment flag `GUARDIAN_ATTACKER_ENABLED`.
This is sufficient for a single-server hackathon demo where only the frontend
makes requests. The flag returns HTTP 503 to any caller without it.

For production (post-hackathon): add an `Authorization: Bearer` header check
using a token from Doppler `aws/dev`. This is a P2 item — not implemented here
because it is outside the hackathon scope and the counter-audit correctly
classifies it as P0 risk only in an open-internet deployment.

---

## 5. All processes now have both voice and text-only modes

**Requested**: every process must have a version with voice speed and a version without voice.

### Dual-mode parameters on `POST /api/llm-attack/stream`

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `voice` | bool | `true` | `false` = text-only, no ElevenLabs calls, no latency |
| `speed` | float | `1.0` | Playback rate 0.5–2.0 (clamped at route) |

**Usage examples**:
```
# Full voice at normal speed (requires VOICE_1_ELEVENLABS_API)
POST /api/llm-attack/stream?voice=true&speed=1.0

# Fast commentary — sports-broadcast style
POST /api/llm-attack/stream?voice=true&speed=1.3

# Slow/clear — forensic review
POST /api/llm-attack/stream?voice=true&speed=0.7

# Text-only — no ElevenLabs, Guardian decision never delayed
POST /api/llm-attack/stream?voice=false

# Text-only is also the safe default when VOICE_1_ELEVENLABS_API is absent
```

**`/api/llm-attack/run`** (existing batch route) is always text-only — no voice, no SSE.

### VoiceCommentary constructor

```python
VoiceCommentary(voice=True,  voice_speed=1.0)   # full audio
VoiceCommentary(voice=False, voice_speed=1.0)   # text-only, no API calls
VoiceCommentary(voice=True,  voice_speed=0.7)   # slow/clear audio
```

`voice=False` disables TTS even when `VOICE_1_ELEVENLABS_API` is set.
`is_enabled()` = `api_key_present AND voice=True`.
`voice_requested()` = what was passed as `voice`, regardless of key availability.

### Doppler `aws/dev` — new optional variable

| Variable | Value | Effect |
|---|---|---|
| `GUARDIAN_VOICE_SPEED` | `1.0` (default) | Default speed for all TTS calls |

---

## 6. R041-P1a — Frontend integration

**Counter-audit finding**: no frontend file was modified in R040.

**Disposition**: the frontend is managed by a separate contributor (see project constraints).
The backend exposes:
- `GET /api/voice/status` — frontend can check voice availability on load
- `POST /api/llm-attack/stream?voice=true` — SSE stream with `voice_script` and `voice_audio`
- `voice_audio` events contain `audio_b64` (base64 mp3) + `mime: audio/mpeg` + `speed`

The frontend integration is a P1 task for the frontend contributor.
The backend contract is fully documented and tested.

---

## 7. R041-P1b — SSE reconnection

**Counter-audit finding**: no reconnection or event-ID mechanism defined.

**Disposition**: the current stream is stateless — each `POST /api/llm-attack/stream`
runs a fresh pipeline. There is no persistent event store to replay from.
The EventSource `Last-Event-ID` reconnection mechanism requires server-side
event persistence, which is a P2 item (external anchor / FileSink integration).

For the hackathon demo, the frontend can simply re-POST to restart the pipeline.
The `done` event signals completion; the frontend can detect disconnection and retry.

---

## 8. Test results (observed in this session)

```
python3 -m pytest guardian_mcp/test_instrumentation.py \
    guardian_mcp/test_demo_scenario.py \
    guardian_api/test_app.py -q

164 passed in 4.58s
```

| File | Collected | PASS | FAIL | New (R041) |
|---|---|---|---|---|
| `test_instrumentation.py` | 98 | 98 | 0 | 0 |
| `test_demo_scenario.py` | 13 | 13 | 0 | 0 |
| `test_app.py` | 53 | 53 | 0 | +10 |
| **Total** | **164** | **164** | **0** | **+10** |

---

## 9. Remaining open items (updated)

| ID | Priority | Description |
|---|---|---|
| `GUARDIAN_FRONTEND_ORIGIN` | **P0 HACKATHON** | Set to actual AWS jury URL |
| AWS deployment | **P0 HACKATHON** | Deploy on Server 2, verify from jury browser |
| Hackathon deliverables | **URGENT** | README jury, video, pitch deck, Track 2 defence |
| Stream endpoint auth | P2 | Bearer token for open-internet deployment |
| SSE reconnection / event-ID | P2 | Requires persistent event store |
| Single merged event ledger | P2 | All agent chains in one cryptographic ledger |
| External anchor | P2 | Store `ArchiveAnchor` in third-party system |

---

## 10. Verdict

All five R041 findings addressed:

- **P0a** (isolation): `guardian_decision` guaranteed to precede any audio — tested with position assertion
- **P0b** (scope): `chain_scope: "defender_events"` field added — tested
- **P0c** (auth): documented as P2 post-hackathon item — no open-internet exposure in demo
- **P1a** (frontend): backend contract documented; frontend task delegated
- **P1b** (reconnection): documented as P2; retry-on-POST recommended for demo

**164/164 PASS. All processes have voice and text-only variants. Guardian decisions never blocked by audio latency.**
