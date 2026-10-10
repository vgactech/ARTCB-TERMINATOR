# ARTCB TERMINATOR frontend

Interactive security-operations dashboard for demonstrating how Guardian detects, blocks, records, and replays a hostile multi-agent action.

## What the demo shows

- A four-agent path: Orchestrator, Attacker, Propagator, and Defender
- An animated attack simulation ending in a blocked tool action
- Policy, execution, evidence, and final-protection verdicts
- Unique evidence, session, and run identifiers
- A nine-stage forensic event timeline
- R0/R1 replay verification and a deliberately failed tamper replay
- Responsive, keyboard-accessible UI with reduced-motion support

## Run locally

Requirements: Node.js 20 or newer and npm.

```powershell
cd frontend
npm install
npm run dev
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

This frontend is currently a self-contained demonstration. The simulation uses local UI state and generated browser UUIDs; it does not yet call the Rust or Python backend. Keeping that boundary explicit makes the demo safe to run while backend endpoints and response contracts are finalized.

When the API contract is ready, replace the local `runSimulation` sequence in `src/App.tsx` with an API client while retaining the existing loading, success, blocked, replay, and error presentation states.
