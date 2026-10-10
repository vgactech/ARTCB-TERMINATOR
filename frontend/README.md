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

Requirements: Node.js 20 or newer and npm.

Start the backend from the repository root in the first PowerShell window:

```powershell
python -m pip install -r guardian_api\requirements.txt
python -m uvicorn guardian_api.app:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second PowerShell window:

```powershell
cd frontend
npm install
npm.cmd run dev
```

Open the local address printed by Vite, normally `http://localhost:5173`, and select **Run attack simulation**.

## Validate a change

```powershell
npm run lint
npm run build
npm run preview
```

The production bundle is written to `dist/` and is intentionally excluded from Git.

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
