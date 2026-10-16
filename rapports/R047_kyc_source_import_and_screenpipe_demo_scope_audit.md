# R047 — KYC Source Import, Private Competition Coordination, and Screenpipe Incident Demo Audit

**Date:** 16 October 2026  
**Status:** Repository reconnaissance complete; source import is blocked pending rights/provenance decision; no application code changed.  
**Target report repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `experiment/artcb-api-mcp-integration`  
**Scope:** This report only. It does not modify ARTCB core, the frontend, KYC application code, VLC&ARTCB, secrets, runtime configuration, or logs.

## 1. Executive decision

The competition plan is now clearer: deliver a demonstrable defensive incident in which a KYC-related failure occurs during a controlled, real-time cyberattack simulation; show the event timeline and defensive response in the frontend; and use Screenpipe as optional operator-context retrieval, not as the authority for security decisions.

The KYC destination repository, `vgactech/artcb_kyc`, is currently empty. The proposed source, `lynadatacraft/atelier-model-thinking-kyc`, is public and substantial, but its repository metadata reports no license and the authenticated GitHub account has read-only access to that source. The source tree response is truncated at 1,000 entries and already shows 823 files / 177 directories, while the repository reports a size of 91,503 KB. The visible tree contains no LICENSE, COPYING, or NOTICE file. Therefore, an immediate wholesale mirror into `artcb_kyc` is **not approved by this audit** until permission or applicable reuse rights are confirmed. Public visibility alone is not a license to republish the entire codebase.

This is a concrete blocker, not a reason to abandon the demo. In parallel, use a clearly synthetic KYC fixture and a small adapter contract so frontend integration can proceed without copying the source repository. Obtain written permission or a suitable license from the source owner, then import the exact pinned commit with provenance and checksums if authorized.

## 2. Expertise activated

- Defensive cybersecurity and controlled incident simulation.
- KYC workflow threat modeling and test-fixture design.
- GitHub repository governance, provenance, access control, and software supply-chain review.
- Frontend/backend integration and event-contract design.
- Screenpipe context retrieval, privacy boundaries, and data minimization.
- Evidence integrity, incident replay, and acceptance-test design.
- Competition demo narrative and technical claim validation.

## 3. Repository synchronization and verified state

The following state was read from GitHub on 16 October 2026:

| Repository | Observed state | Consequence |
|---|---|---|
| `vgactech/ARTCB-TERMINATOR` | Private; default branch `main`; report branch `experiment/artcb-api-mcp-integration` exists; current linked account has admin/push permission | Keep this coordination/report repository private. Re-check visibility after any repository administration change. |
| `vgactech/artcb_kyc` | Public; size 0 KB; Git repository empty; default branch `main`; current linked account has admin/push permission | It currently contains no commit/tree to preserve or merge. |
| `lynadatacraft/atelier-model-thinking-kyc` | Public; default branch `main`; reported size 91,503 KB; current linked account has pull but not push permission; no license metadata and no visible LICENSE/COPYING/NOTICE file in the returned tree | Read access is confirmed; write access to the source is not. Copying the full repository needs a rights/provenance decision first. |
| `vgactech/artcb_TERMINATOR_FRONTEND` | Public; default branch `main`; observed tree contains `rapports/R001_mediapipe_jarvis_3d_single_hand_frontend_specification.md` | The checked-in artifact is a design specification, not evidence that a working frontend or Screenpipe integration already exists. |
| `vgactech/artcb` | Private; default branch `main`; current linked account has admin/push permission | Treat as the protected core. Do not change it as part of this report-only operation. |

### What was and was not changed

Only this report is being added to `ARTCB-TERMINATOR`. No source or destination repository contents were changed by this audit. No push was made to `artcb_kyc`, no files were copied, no logs were uploaded, and no application was deployed. The private visibility of `ARTCB-TERMINATOR` was checked and confirmed.

## 4. KYC source import: process, problem, and correction

### Process — what “clone into artcb_kyc” means

A normal Git clone creates a local working copy and retains Git history. Publishing that history into a different, already-created repository is a separate operation: it must deliberately choose whether to preserve the source commit graph, import only a snapshot, or create a fork. The result should record the original URL, exact source commit, import date, and integrity checks.

### Problem — the requested source is not an empty or obviously licensed starter

The source repository is much larger than the empty destination. The returned recursive tree is truncated at 1,000 entries, so the full file inventory has not yet been established through this API response. Repository metadata reports no license, and the visible tree has no license/notice file. This means the audit cannot confirm permission to reproduce the complete repository in another owner's repository. The source owner also has not granted the connected account write permission.

There is a second operational concern: KYC projects can contain realistic company, identity, financial, or compliance material. The visible source paths include participant packs, business records, corrections, and structured JSON datasets. Before using any of this in a live demo, classify the data and verify whether it is synthetic, licensed for redistribution, and safe to display. Do not send real personal or financial data to the frontend, logs, Screenpipe, or a public repository.

### Correction — immediate safe path

**P0 — Rights and provenance gate**
1. Request written permission from the source owner to copy the repository into `vgactech/artcb_kyc`, or obtain a license that clearly permits the intended copying and redistribution.
2. Pin the exact source commit SHA at import time. Do not import a moving `main` branch without recording its resolved commit.
3. Obtain a complete tree/file inventory, identify large files and sensitive datasets, and check for secrets or personal data before publishing.
4. Preserve upstream attribution, notices, and license text if the owner supplies or confirms them. Do not invent a license or remove provenance.
5. Record import method, original URL, commit SHA, file counts, checksums, and exclusions in an import manifest.

**P0 — Continue the demo without waiting**
- Add a small, explicitly synthetic KYC incident fixture in the authorized demo repository only after its owner and scope are confirmed.
- Model a single deterministic failure, such as a mismatch between the expected KYC decision and a deliberately corrupted or stale event, without using real identities or external targets.
- Keep the fixture clearly labelled `SIMULATED` in the UI and event payload. Do not present the simulation as an observed real-world attack.
- Keep the fixture separate from the eventual imported source so it can be removed or replaced without rewriting the demo architecture.

## 5. Competition demo: one complete defensive incident

The strongest demonstration is not a cinematic animation by itself. It is one end-to-end, reproducible story where each visible state is tied to an event or a test assertion.

### Proposed flow

1. **Scenario controller:** starts a bounded, local simulation with a unique run ID and reset control.
2. **KYC fixture/adapter:** emits a synthetic KYC request and a deliberately injected failure condition.
3. **Event adapter:** normalizes the event into a stable schema with event ID, timestamp, run ID, source, severity, entity reference, evidence reference, and simulation/observation label.
4. **ARTCB/Guardian decision adapter:** reports the actual decision available from the authorized core integration. If not connected, the UI must say `SIMULATED DECISION` rather than imply the core made the decision.
5. **Frontend timeline:** renders events in order and shows detection, decision, containment, and recovery as distinct states.
6. **Screenpipe context adapter:** optionally retrieves permitted local operator context to help explain what the operator saw or did. Each result is tagged `CONTEXT EVIDENCE`, with provenance and timestamp when available.
7. **Evidence inspector/replay:** lets a reviewer inspect the event payload, source, timestamps, checksums where used, and the difference between observed evidence and inferred explanation.
8. **Reset/offline path:** resets the scenario and continues to work when Screenpipe is unavailable or permission is denied.

### Why the labels matter

- **Observed:** a source actually emitted or recorded the event.
- **Decision:** a policy engine or adapter returned a decision.
- **Confirmed containment:** a measurable result confirms the threat was blocked or isolated.
- **Context evidence:** supporting operator context retrieved from Screenpipe; not authoritative KYC state.
- **Simulated:** deliberately generated by the demo controller.
- **Inferred:** a reasoned interpretation, not a directly observed fact.

Never display “blocked,” “contained,” or “recovered” merely because an animation completed. The state must follow a confirmed response or be explicitly marked as simulated.

## 6. Screenpipe: correct role and boundaries

### Process

Screenpipe can provide local screen/audio context and search/retrieval capabilities depending on the installed version, permissions, configuration, and supported APIs. The frontend should consume it through a small adapter rather than hardwire the UI to implementation details.

### Problem

Screenpipe memory/context is not automatically equivalent to blockchain properties such as tamper-evident history, distributed consensus, independent verification, or durable integrity guarantees. It can also expose private screen/audio content if collection is enabled without clear scope and consent.

### Solution

- Use Screenpipe as an optional operator-context source, not as the KYC database, authorization engine, or sole evidence-integrity mechanism.
- Make access opt-in and explain which local context is queried.
- Store minimal metadata and references; avoid copying raw screen/audio content into frontend state, public issues, telemetry, or logs.
- Provide a health check, explicit unavailable state, bounded query scope, permission-denied fallback, and a demo mode that works offline.
- Treat returned content as untrusted context: sanitize it, label its origin, and never allow it to execute instructions or override a security decision.
- If replacing blockchain-backed behavior, map every relied-upon guarantee to an alternative and add a test for that guarantee. Use signed records, append-only storage, hashes, or an independent verifier only where the actual threat model requires them.

Official references to validate against the version installed for the event:
- Screenpipe repository: https://github.com/screenpipe/screenpipe
- Installation: https://screenpipe.com/how-to-install
- CLI reference: https://docs.screenpi.pe/cli-reference
- Security/privacy: https://screenpipe.com/security
- License file: https://github.com/screenpipe/screenpipe/blob/main/LICENSE.md

## 7. Integration contract and minimum acceptance gates

### Minimum event fields

Every event should have: `event_id`, `run_id`, `timestamp`, `event_type`, `source`, `severity`, `status`, `simulation`, `provenance`, and optional `entity_ref`, `evidence_ref`, `correlation_id`, and `decision_ref`.

### Acceptance criteria

- [ ] A fresh run produces the same ordered synthetic incident sequence.
- [ ] Every displayed event has a stable ID and provenance.
- [ ] Simulated activity is visibly distinguished from live telemetry.
- [ ] A KYC failure can be reproduced and reset without contacting a real target.
- [ ] A core/Guardian decision is shown as real only when the adapter returns a verifiable result.
- [ ] Screenpipe is optional; denied permission or unavailable service does not break the incident timeline.
- [ ] Screenpipe results are labelled as context and cannot change authoritative KYC state or security decisions.
- [ ] The UI does not claim containment or recovery without a confirming result.
- [ ] Replay exposes source and timestamps and detects tampering where integrity is claimed.
- [ ] No secrets, raw personal KYC data, private screen/audio captures, or runtime logs are committed.
- [ ] `ARTCB-TERMINATOR` remains private.

## 8. Repository responsibilities and scope control

- **ARTCB-TERMINATOR:** private coordination and numbered English audit reports for the competition team.
- **artcb_TERMINATOR_FRONTEND:** frontend implementation and presentation; current evidence only confirms a design specification.
- **artcb_kyc:** intended KYC integration target; currently empty and awaiting an authorized, traceable source import or synthetic fixture.
- **artcb:** protected core repository. Any future change must be separately scoped and explicitly authorized; this report does not modify it.
- **VLC&ARTCB:** out of scope unless explicitly requested.
- **Screenpipe:** optional context provider, not a replacement for every blockchain guarantee.

Do not push runtime logs, real KYC material, captured screen/audio content, credentials, or secrets into any repository.

## 9. Priorities

**P0 — Today**
1. Keep `ARTCB-TERMINATOR` private.
2. Request source-copy permission or a suitable license from the upstream KYC repository owner.
3. Continue the UI integration against a synthetic, deterministic KYC incident fixture, clearly marked as simulated.
4. Inspect the actual frontend package/build/test setup and the ARTCB integration contracts before claiming that the components are wired together.

**P1 — After rights are clear**
1. Import the pinned source commit using a documented, reproducible method.
2. Scan the full import for secrets, sensitive data, oversized files, and licensing notices.
3. Run available tests and add a regression test for the chosen KYC failure.
4. Connect the event adapter, core/Guardian adapter, timeline, replay, and optional Screenpipe context.

**P2 — After the vertical slice passes**
1. Add more attack scenarios.
2. Add 3D visualization, hand gestures, voice narration, and presentation polish.
3. Add automated end-to-end checks for offline mode, replay, and evidence integrity.

## 10. Final audit statement

The highest-priority issue is confirmed: `vgactech/artcb_kyc` is empty, while the proposed upstream KYC repository is a large public repository with no declared license visible in the inspected metadata/tree and no write access for the connected account. A blind full-repository copy would create unresolved rights, provenance, data-classification, and supply-chain risks. Therefore, this audit does not claim that the requested import was completed.

The fastest responsible path is to request explicit reuse permission while building the live-looking incident demonstration with synthetic fixtures. This allows the competition demo to progress immediately without misrepresenting a simulation as a real attack or importing unverified KYC data. Once permission is confirmed, import a pinned commit, record provenance, scan the contents, and validate the test suite before wiring the imported KYC behavior into the frontend.

**Change statement:** this report is the only intended change in this operation. No source repository, destination KYC repository, frontend code, ARTCB core, VLC&ARTCB, secrets, deployments, or runtime logs were modified. The ARTCB-TERMINATOR repository was verified private before writing this report.
