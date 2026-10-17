# R076 — KYC Liveness Gate (MediaPipe) + KYC Tab UI Redesign

**Date:** 2026-10-17
**Project:** `vgactech/ARTCB-TERMINATOR`
**Base commit:** `cbf19b1` (HEAD = R075, branch `main`)
**Scope:** browser + backend human-presence (liveness) engine, and KYC tab layout redesign.
**Mode:** `GUARDIAN_LIVENESS_ENABLED=true` (default), TTL `60 s`. Changes not yet committed at the date of this report.

---

## 1. Summary

Added a **human-presence (liveness) check** based on **hand movement** to the KYC flow, to defeat an automated attacker who would present an identity without being physically present:

- **100% browser-side MediaPipe detection** (MediaPipe Tasks Vision) — **no image leaves the machine**; only pixel-free numbers (frame count, movement score, directions, pinch ratio) are transmitted.
- **Single-use nonce challenge** issued by the backend (random challenge: `left_to_right | raise_hand | pinch | wave`), which neutralizes replay of a recorded capture.
- **R0 evidence chaining**: every verification produces a signed terminal event in the Guardian SHA-256 chain.
- **Server-enforced verdict**: `APPROVED ⟺ identity_ok ∧ blocked ∧ chain_valid ∧ liveness_ok`. A `FAIL` forces `REJECTED`; `SIMULATED`/absent never blocks (offline demo stays functional).
- **5th narration moment** (ElevenLabs commentary) + a dedicated section in the forensic PDF.
- **UI redesign** of the KYC tab: the first view is reduced to *identity | camera*, and results are revealed below the first view on clicking "Lancer KYC complet".

**Status:** ✅ 214 Python tests PASS + 18 frontend (vitest) tests PASS. Frontend build OK, lint OK (2 pre-existing warnings).

---

## 2. Context & problem

The KYC flow relied on identity (documentary fields) and the Guardian decision, with no proof that a **human** was actually in front of the camera. An attacker could therefore have an identity processed without physical presence, or replay a recorded capture.

Three requirements drove the design:

1. **Privacy** — no image exfiltration; heavy computation stays local.
2. **Anti-replay** — a random, single-use challenge, verifiable server-side.
3. **Demo non-regression** — the scenario must remain runnable without a camera or network (`SIMULATED` fallback).

---

## 3. Architecture

```
   BROWSER (frontend/)                            BACKEND (guardian_api/)
 ┌───────────────────────────┐                 ┌──────────────────────────────┐
 │ getUserMedia (camera)     │                 │ GET  /api/liveness/status    │
 │ MediaPipe HandLandmarker  │                 │ POST /api/liveness/challenge │
 │  ├─ skeleton (21 pts)     │                 │ POST /api/liveness/verify    │
 │  └─ gesture.ts (analysis) │                 │                              │
 │       ↓ numbers only      │  observation    │ LivenessController           │
 │  POST /api/liveness/verify ───────────────▶ │  ├─ single-use nonce + TTL   │
 │       ◀──────────────────────── verdict      │  ├─ movement/pinch thresholds│
 └───────────────────────────┘                 │  ├─ evidence → R0 chain      │
                                               │  └─ PASS|FAIL|SIMULATED      │
                                               │                              │
   POST /api/kyc/stream?liveness_token=… ─────▶│ kyc_stream.py                │
       ◀─ SSE (session → liveness → attack      │  enforced verdict + PDF      │
           → decision → result)                 └──────────────────────────────┘
```

**Observation transmitted** (`POST /api/liveness/verify` contract):
`challenge_id, nonce, gesture, hand_frames, movement_score, directions, pinch_ratio, gesture_matched, duration_ms, simulated?`

**Verdict returned**:
`liveness ∈ {PASS, FAIL, SIMULATED}, reason, human_proven, gesture, evidence_id, guardian_event_id, data_source`

---

## 4. Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Where MediaPipe runs | Browser | no image on the wire; no server GPU load |
| Anti-replay | Single-use nonce (`secrets`) + TTL | a recorded capture cannot answer a random challenge |
| MediaPipe delegate | `CPU` default, `GPU` opt-in with fallback | WebGL fails headless (`emscripten_webgl_create_context() returned error 0`) |
| Verdict rule | `APPROVED ⟺ identity_ok ∧ blocked ∧ chain_valid ∧ liveness_ok` | blocks `FAIL`, allows the offline demo |
| Liveness disabled/absent | `SIMULATED` / `SKIPPED` = non-blocking | demo works without camera or network |
| Model loading | runtime CDN + offline fallback | machine sovereignty, no heavy build |

---

## 5. Backend changes

### `guardian_api/liveness.py` (NEW — 315 lines)
`LivenessController`: challenge issuance (`secrets`, single-use, TTL), `verify()` (nonce/expiry/replay/threshold checks), results `PASS | FAIL | SIMULATED`, `result_for(challenge_id)`, purge, event counter. Owns a `GuardianMCPInstrumentation(agent_id="agent:liveness-guard")` instance; module singleton `liveness_controller`. Explicit `simulated: bool` parameter on `verify()`.

### `guardian_api/app.py`
| Route | Purpose |
|---|---|
| `GET /api/liveness/status` | availability (enabled/TTL) |
| `POST /api/liveness/challenge` | issues a nonce challenge |
| `POST /api/liveness/verify` | verifies the observation (`LivenessObservationBody`, `simulated` field) |
| `/api/kyc/stream` | new `liveness_token` parameter |

### `guardian_api/kyc_stream.py`
- New SSE stage `liveness_check` after `kyc_identity_check`.
- Re-sequenced order: `0=session, 1=liveness, 2=attack, 3=decision, 4=result`.
- **Enforced verdict**: `if not liveness_ok: → REJECTED`.
- `liveness` / `human_proven` exposed in `kyc_result`.
- PDF section "PREUVE DE PRESENCE HUMAINE (LIVENESS)" (fpdf + `_minimal_pdf`).

### `guardian_mcp/`
- `instrumentation.py`: additive `record_decision(*, tool_name, decision, reason, arguments, duration_ms, output_summary)` → one chained terminal `guardian.signal` event.
- `voice_commentary.py`: `liveness_check` commentary branch (5th moment).

---

## 6. Frontend changes

### New modules
| File | Purpose |
|---|---|
| `src/liveness/gesture.ts` | pure landmark analysis (hand center, pinch ratio, directions), `GestureDetector` |
| `src/liveness/handLandmarker.ts` | MediaPipe CDN loader (`@mediapipe/tasks-vision@1.1.1`), `HAND_CONNECTIONS` (21 joints), `CPU` delegate |
| `src/components/LivenessGate.tsx` | camera + skeleton overlay (lines then joints) + demo mode; `forwardRef` (`start`/`demo`), `showControls`, `onBusyChange` |
| `src/voice/audioQueue.ts` | narration audio playback queue |

### `KycPanel.tsx` redesign
The layout moves from two parallel columns to **two stacked sections**:

- **Section A — first view**: `[ identity fields (left) ] [ camera (right) ]` as 2 inline, then below the fields: **Voix ON/OFF** button, **Démarrer le défi (caméra)** / **Mode démo sans caméra** buttons, **Lancer KYC complet** button, PDF link. The camera thus gets the full height of its column.
- **Section B — results (revealed on click)**: metrics (Attaques/Bloquées/Taux), KYC report, Forensic Timeline, Guardian 4-agent graph. Revealed and scrolled into view on launch (`resultsRef.scrollIntoView`).
- The narration **speed selector has been removed** (fixed at 1.0×).

### Other
- `App.tsx`: KYC tab full width (`max-w-none`), HUD header kept; the graph is no longer a fixed overlay.
- `components/LiveGuardianGraph.tsx`: `embedded` prop (inline flow vs HUD).
- `api/guardian.ts`: `Liveness*` types + `fetchLivenessStatus` / `createLivenessChallenge` / `verifyLiveness`; `KycResult.liveness` / `.human_proven`.
- **Automatic camera close**: `LivenessGate.submitObservation` calls `stopCamera()` in a `finally` block (stops all `MediaStreamTrack`s, `srcObject = null`, clears the canvas) as soon as verification finishes (PASS/FAIL/error). Same on detection error and camera/model unavailable.

---

## 7. KYC sequence

| # | Step | SSE event |
|---|---|---|
| 0 | Session opened | `session_opened` |
| 1 | Human presence | `liveness_check` |
| 2 | Simulated LLM attack | `attack_generated` |
| 3 | Guardian decision | `guardian_decision` |
| 4 | End / result | `kyc_result`, `done` |

---

## 8. Tests & evidence

```bash
python3 -m pytest guardian_api guardian_mcp -q        # 214 passed
cd frontend && npm test                               # 18 passed (2 files)
cd frontend && npm run lint                           # 0 errors (2 pre-existing warnings)
cd frontend && npm run build                          # OK (tsc -b && vite build)
```

| Suite | Result |
|---|---|
| Python (`guardian_api` + `guardian_mcp`) | **214 passed** |
| Frontend vitest (`gesture.test.ts` 14 + `audioQueue.test.ts` 4) | **18 passed** |
| Rust `#[test]` | 45 counted — `cargo` not installed in this environment |
| **Expected total** | **259 = 214 + 45** |

Notable functional coverage (`guardian_api/test_liveness.py`): unit controller + API + KYC integration (`PASS→APPROVED`, `FAIL→REJECTED`, `SKIPPED→APPROVED`, PDF section).

---

## 9. Limitations & caveats

- **Liveness is client-attested and therefore spoofable**: the verdict relies on numbers supplied by the browser. A modified client can forge them. To be documented as such — this is not certified anti-spoofing.
- **MediaPipe = heuristic**: skeleton and gesture detection is probabilistic, not biometric authentication.
- **GPU/WebGL delegate unavailable** in headless environments (`StartGraph failed … emscripten_webgl_create_context() returned error 0`) → `CPU` delegate by default.
- **Real camera capture cannot be validated here** (no webcam headless); the automatic camera close is only verified by logic (track stopping).
- `getUserMedia` requires `localhost` or HTTPS; Chromium browsers recommended.
- `cargo` absent → the 45 Rust tests are **counted**, not run, in this environment.

---

## 10. Files added / modified

### Added
| File | Lines |
|---|---|
| `guardian_api/liveness.py` | 315 |
| `guardian_api/test_liveness.py` | 286 |
| `frontend/src/components/LivenessGate.tsx` | 352 |
| `frontend/src/liveness/gesture.ts` | 217 |
| `frontend/src/liveness/gesture.test.ts` | 157 |
| `frontend/src/liveness/handLandmarker.ts` | 84 |
| `frontend/src/voice/audioQueue.ts` | 91 |
| `frontend/src/voice/audioQueue.test.ts` | 111 |
| `frontend/vitest.config.ts` | — |

### Modified
`guardian_api/app.py`, `guardian_api/kyc_stream.py`, `guardian_api/requirements.txt`, `guardian_api/test_app.py`, `guardian_mcp/instrumentation.py`, `guardian_mcp/voice_commentary.py`, `frontend/src/App.tsx`, `frontend/src/api/guardian.ts`, `frontend/src/components/KycPanel.tsx`, `frontend/src/components/LiveGuardianGraph.tsx`, `frontend/src/components/ForensicPanel.tsx`, `frontend/src/forensic/phases.ts`, `frontend/vite.config.ts`, `frontend/tsconfig.app.json`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/README.md`, `.gitignore`.

**Overall diff:** 18 modified files, +1571 / −252 (excluding new files).

---

## 11. Cleanup

- `frontend/dist/` removed (build artifact, gitignored).
- `frontend/web_console_error.txt` removed (WebGL debug trace).
- `AGENTS.md` is **gitignored** and stays local (not committed).
- `README.md` / `SUBMISSION_HACKATHON.md` carry stale test counts — **`pytest` is the reference**.

---

## 12. Verdict

**Implementation: delivered and green — 214 Python tests + 18 frontend tests PASS, build and lint OK.**

The KYC flow now requires, when liveness is enabled, a human-presence proof via a single-use nonce challenge, chained into the R0 evidence, with a server-enforced verdict and a non-blocking `SIMULATED` fallback for the offline demo. Video capture remains strictly local; only numbers cross the network.

**Explicit caveat:** the presence proof is *client-attested* and therefore spoofable; it is a practical anti-bot barrier for the demo, **not** certified anti-spoofing. This limitation is acknowledged and documented.
