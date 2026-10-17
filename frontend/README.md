# ARTCB TERMINATOR frontend

Interactive security-operations dashboard for demonstrating how Guardian detects, blocks, records, and replays a hostile multi-agent action.

## What the demo shows

- A real four-agent path: Orchestrator, Source/Attacker, Propagator, and Defender
- Four selectable backend scenarios covering ALLOW, BLOCK, and ESCALATE
- Policy, execution, evidence, and chain-verification verdicts from Guardian
- Unique evidence, session, and run identifiers
- The real INTENT and TERMINAL event records created by each request
- R0 chain verification and a deliberately failed tamper replay
- Responsive, keyboard-accessible UI with reduced-motion support

## Run locally

Requirements: Node.js 20+ and npm, Python 3.10+.

The Vite dev server proxies `/api` to the Guardian backend. The target defaults to
`http://127.0.0.1:8002` (the `start_guardian.sh` port) and can be overridden with
`VITE_API_PROXY`.

Start the backend from the repository root:

```bash
pip install -r guardian_api/requirements.txt
python3 -m uvicorn guardian_api.app:app --host 127.0.0.1 --port 8002
# or: ./start_guardian.sh   (same port, plus KYC self-test; set GUARDIAN_PORT to change)
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (normally `http://localhost:5173`). To point the browser
directly at a different backend origin instead of the proxy, set `VITE_API_URL`.

## Validate a change

```bash
npm run lint
npm run build
npm test          # vitest — voice audio queue + liveness gesture analysis
npm run preview
```

The production bundle is written to `dist/` and is intentionally excluded from Git.

## KYC voice narration

The KYC tab can narrate the five key moments of the scenario (session start, liveness
challenge, attack detected, Guardian BLOCK, final verdict) with ElevenLabs commentary.
`voice_script` events always provide caption text; `voice_audio` events (base64 mp3) appear
only when `VOICE_1_ELEVENLABS_API` is set on the backend. Use the **Voix ON/OFF** toggle
and the speed selector in the panel; without a key the run still completes and captions
remain.

## KYC liveness (hand-movement challenge)

The KYC panel includes a **Preuve de présence humaine** gate: the backend issues a random
single-use gesture challenge (`left_to_right`, `raise_hand`, `pinch`, `wave`) with a nonce,
and the browser must prove a live human performed it. MediaPipe Tasks Vision is loaded from
a CDN at runtime (jsDelivr + Google Storage model) and runs entirely in the browser —
camera frames never leave the device; only a pixel-free observation (frame count, movement
score, directions, pinch ratio) is POSTed to `/api/liveness/verify`.

- **Démarrer le défi (caméra)** requires `getUserMedia` (localhost or HTTPS) and a CDN
  reachable for MediaPipe. Requires Chrome/Edge for best results.
- **Mode démo sans caméra** skips MediaPipe and returns a `SIMULATED` result — useful for
  offline demos and always clearly marked.
- The resulting challenge id is passed as `liveness_token` to `/api/kyc/stream`. With it,
  the verdict is enforced: `APPROVED` requires a passed liveness check (plus identity,
  blocked attack, and an intact R0 chain). A `FAIL` forces `REJECTED`; `SIMULATED`/absent
  never block. Backend env: `GUARDIAN_LIVENESS_ENABLED` (default `true`),
  `GUARDIAN_LIVENESS_TTL` (default `60`s).

Caveat: client-attested liveness is spoofable by a scripted client. This is a
challenge-response demo control, not a certified anti-spoof mechanism.

## Technology

- React 19 and TypeScript
- Vite 8
- Tailwind CSS 4
- Framer Motion
- Lucide icons
- Oxlint

## Integration status

The dashboard calls the Python Guardian API through Vite's `/api` development proxy. Guardian performs the real policy evaluation and returns its decision, execution state, event records, evidence identifier, chain verification, and tamper-test result. The interface reports an offline error if the API is not running instead of substituting mock data.

Every selectable scenario creates four distinct agent instances in the backend. The Orchestrator opens a shared session, the Source constructs a hashed request, the Propagator records the causal relay, and the Defender evaluates that same request. The returned agent trace drives the dashboard visualization. These are four collaborating instances inside one Python API process, not four independently deployed network services.

The Rust core is a separate security implementation in this repository. The current HTTP path uses the Python MCP instrumentation; it does not load the optional Rust/PyO3 binding.
