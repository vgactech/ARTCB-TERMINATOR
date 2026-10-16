# R046 — Frontend/KYC Live-Incident Demo and Screenpipe Context Integration Audit

**Date:** 2026-10-16  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `experiment/artcb-api-mcp-integration`  
**Report sequence:** Follows R045 on the experiment branch  
**Scope:** Read-only review of the current frontend and KYC repositories, definition of a controlled live-incident demo, and a safe integration plan for Screenpipe as contextual evidence.  
**Change boundary:** This report is the only intended repository change. No application code, tests, deployment settings, secrets, runtime state, logs, frontend repository, KYC repository, ARTCB core, or VLC&ARTCB files are modified. No logs are committed.

---

## 1. Executive decision

**Verdict: DEMO DESIGN CAN PROCEED; END-TO-END IMPLEMENTATION AND THE KYC FAILURE ARE NOT YET VERIFIED.**

The intended demonstration should show a realistic, time-correlated defensive incident in a controlled test environment: a simulated attack attempts to abuse a KYC workflow; telemetry records the attempt; ARTCB/Guardian correlates the evidence, evaluates the policy, and blocks or contains the action; the frontend displays the evolving graph and timeline; and the operator can inspect the evidence and replay the incident afterward.

The demonstration must not claim to reproduce a specific defect in `artcb_kyc` until that repository contains inspectable source or a reproducible test case. GitHub currently reports `vgactech/artcb_kyc` as empty. Its `main` branch exists, but fetching a README returns GitHub's explicit “This repository is empty” response. This is a hard dependency, not a reason to invent a KYC bug.

The frontend repository currently exposes a single latest commit, `88b124bd7c185c42bcafc3448570bb42df321a26`, titled “docs: add R001 MediaPipe single-hand 3D frontend specification.” The commit adds `rapports/R001_mediapipe_jarvis_3d_single_hand_frontend_specification.md`; it is a design document, not evidence of a working UI or a Screenpipe integration. The specification itself says live backend integration and production readiness remain to be validated. No frontend build, browser session, or live integration test was run as part of this report.

The private `ARTCB-TERMINATOR` repository remains **private**. This report does not change repository visibility, merge branches, deploy services, or modify any application code.

## 2. Expertise activated

- Defensive cybersecurity and controlled attack simulation.
- KYC workflow threat modeling and application security.
- Frontend architecture, event-driven visualization, and incident replay.
- Screenpipe API/MCP integration and local-context privacy.
- Distributed tracing, event correlation, and digital forensics.
- Evidence integrity, provenance, and confidence labeling.
- Git repository state, branch continuity, and audit/report governance.
- Demo engineering, acceptance criteria, and failure-mode testing.

## 3. Repository synchronization and observed state

The following state was retrieved from GitHub during this audit.

| Repository | Observed state | Audit consequence |
|---|---|---|
| `vgactech/ARTCB-TERMINATOR` | Private; default branch `main`; main's latest observed commit is `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844` (R043) | Preserve private visibility. R045 is on `experiment/artcb-api-mcp-integration`; do not assume experiment-branch reports are already on main. |
| `vgactech/ARTCB-TERMINATOR` experiment branch | `experiment/artcb-api-mcp-integration` exists; R045 is present at `rapports/R045_operational_delta_live_execution_acceptance_gate.md` | R046 continues the report sequence on this branch without merging or rebasing. |
| `vgactech/artcb_TERMINATOR_FRONTEND` | Public; default branch `main`; latest observed commit `88b124bd7c185c42bcafc3448570bb42df321a26` | Current inspectable evidence is a specification document, not a verified implementation. |
| `vgactech/artcb_kyc` | Public; GitHub reports repository size 0; no README/source could be fetched | KYC behavior and its specific failure cannot currently be reproduced from repository code. |

### Important distinction

A repository existing on GitHub does not prove that its application is implemented, buildable, deployed, or connected to the other repositories. A design specification is not a runtime test. A configured service URL is not proof of a successful request. A successful unit test is not proof of a complete incident lifecycle.

## 4. Process — what the demonstration should show

The demo should tell one traceable story from the first observable signal to the post-incident proof:

1. **Baseline:** display the KYC demo environment, active services, current telemetry coverage, and whether data is live, recorded, or simulated.
2. **Attack initiation:** trigger a predefined, harmless test scenario against a dedicated local/staging KYC fixture. The scenario should model a recognizable abuse pattern, such as repeated invalid verification attempts or a controlled attempt to alter a synthetic verification state. It must not target real people, production accounts, or third-party systems.
3. **Event capture:** the KYC fixture and/or test harness emits structured events with stable event IDs, timestamps, scenario ID, source, and correlation ID.
4. **Guardian evaluation:** the defensive service consumes those events, evaluates an explicit policy, and emits an allow/block/escalate result with the relevant evidence references.
5. **Containment:** the demo records the defensive action and its observable effect. The UI must not display “contained” until a confirming event or test assertion exists.
6. **Context enrichment:** where relevant and consented, Screenpipe search results can provide operator-context evidence, such as which test console or relevant screen state was visible around the incident.
7. **Visualization:** the frontend updates the timeline and causal graph as events arrive, showing source, event time, ingestion time, state, evidence links, and telemetry gaps.
8. **Forensic replay:** the operator can pause visual playback, inspect the original events, follow causal links, and compare the state before and after containment.
9. **Closure:** the demo reports which acceptance assertions passed, which failed, and which telemetry sources were unavailable.

This is a defensive, isolated reproduction of an incident pattern. It is not a claim that a real external system was attacked.

## 5. Problem — the KYC scenario is not yet grounded in source code

### What is known

GitHub reports the KYC repository as empty. The earlier R043/R045 audit history records a KYC test failure and incomplete end-to-end validation, but those historical notes are not a current reproducible test case.

### Why this matters

Without the KYC source, test fixture, logs captured outside the repository, or a precise failure description, the team cannot responsibly identify the exact vulnerable function, expected state transition, or regression test. Guessing the failure would risk demonstrating a fabricated defect and presenting it as a real result.

### Required resolution

Before calling the demo a reproduction of the actual KYC problem:

- Populate or point to the authorized KYC source and its exact commit.
- Identify the failing test or documented incident with input, expected outcome, actual outcome, and environment.
- Reproduce the failure in a dedicated local/staging fixture.
- Preserve the original failure as a regression test.
- Add a defensive test proving that the intended policy detects or blocks the scenario.
- Record test output and artifact hashes outside Git unless the repository's existing report policy explicitly calls for a sanitized summary. Never commit runtime logs, personal data, identity documents, API keys, or production KYC records.

Until these prerequisites are met, label the demo **“controlled simulated KYC incident”**, not “reproduction of the existing KYC bug.”

## 6. Screenpipe — appropriate role and integration boundary

Official Screenpipe materials describe a local-first desktop context system that can capture screen/application context and audio/transcriptions, store data locally by default, and expose a local REST API on port 3030. The documented REST search endpoint is `GET /search`; Screenpipe also offers an MCP integration for compatible clients. See the sources in Section 11.

### Appropriate use in this demo

Use Screenpipe as an **optional context/evidence source**, not as the authoritative security detector or the source of truth for KYC state.

- Check availability through the documented local health endpoint before enabling context enrichment.
- Query only the specific time window and content types needed for the incident.
- Associate a context query with the incident/scenario ID in the demo's own correlation layer.
- Store references, timestamps, result IDs, and integrity metadata where available; avoid duplicating raw screen/audio content unnecessarily.
- Show Screenpipe-derived context as **“operator context”** or **“context evidence”**, visually distinct from signed Guardian/KYC events.
- If Screenpipe is unavailable, denied, or returns no results, the core security demo must still run.
- Make the integration opt-in, explain screen/audio capture, apply app/window/content filters, and avoid recording or displaying secrets, passwords, personal identity data, or unrelated work.
- Keep local-only processing as the default. Any cloud transcription, hosted AI, sync, or export path must be explicitly configured and disclosed.

### What Screenpipe does not prove

A screenshot, OCR result, application title, or audio transcript can help explain the operator's context. It does **not** prove that a KYC transaction succeeded, that a Guardian policy was applied, that a backend event is authentic, or that an attack was contained. Those claims require evidence from the relevant application/service and its tests.

### Licensing gate

Screenpipe's current repository describes its source as source-available and indicates that commercial use may require a license. Before bundling, redistributing, or using it in a commercial competition deliverable, review the current `LICENSE.md` and obtain any necessary permission. Using its documented local API as an external installed tool is different from copying or redistributing its code.

## 7. Proposed event contract for the live graph

The frontend and backend should agree on a small, versioned event envelope before integration. At minimum, each event should carry:

- `event_id`: unique, stable identifier.
- `scenario_id`: identifies the controlled demo run.
- `correlation_id` and optional `parent_event_id`: connect events across the KYC fixture, Guardian, and frontend.
- `source` and `source_type`: e.g. KYC test harness, Guardian, or Screenpipe context adapter.
- `event_type` and `status`: observed action or state transition.
- `event_time` and `ingestion_time`: preserve the original event time and the time the viewer received it.
- `evidence_refs`: references to supporting artifacts, not raw secrets.
- `integrity_status`: verified, failed, unchecked, or not applicable.
- `data_classification`: synthetic, sanitized, or sensitive.
- `mode`: live, simulated, or replay.

The actual serialization must be reconciled with the current API rather than assumed. Unknown fields should be preserved or handled explicitly according to a versioned schema. Missing telemetry must be displayed as a coverage gap, never silently interpreted as “no attack.”

## 8. Architecture recommendation

**Controlled KYC fixture → structured test events → Guardian policy decision → incident event stream → frontend graph/timeline**

In parallel:

**Optional Screenpipe local API → bounded context query → context adapter → clearly labeled context evidence**

The frontend should consume a normalized event stream and should not directly access secrets or privileged security controls. The Screenpipe adapter should be optional and read-only for the demo. It should not be allowed to issue KYC decisions, authorize a transaction, suppress Guardian alerts, or mutate evidence.

Keep these states distinct:

- **Observed:** emitted by a named instrumented source.
- **Policy decision:** returned by Guardian with a decision/evidence reference.
- **Confirmed effect:** validated by a service response or test assertion.
- **Context evidence:** retrieved from Screenpipe and labeled with its provenance.
- **Inferred:** an analytical conclusion that is not directly observed.
- **Simulated:** generated by the controlled scenario harness.
- **Unknown / telemetry gap:** evidence is absent, delayed, or unavailable.

## 9. Priority plan — process, problem, solution

### P0 — Establish the KYC reproduction

**Process:** identify the actual KYC failure and make it repeatable in an isolated fixture.

**Problem:** the repository is empty, so no code-based reproduction can currently be verified.

**Solution:** restore or locate the authorized source, pin its commit, capture the expected/actual behavior, and add a deterministic regression test. Do not label a made-up scenario as the existing defect.

### P0 — Confirm frontend implementation status

**Process:** compare the design specification with actual files, dependencies, build scripts, and browser behavior.

**Problem:** the latest visible frontend commit adds only a specification document; a working UI or Screenpipe integration is not demonstrated by this commit.

**Solution:** inspect the actual current repository tree and CI/build configuration when available; then implement and test the smallest vertical slice: scenario trigger → event ingestion → timeline update → evidence detail. Keep this as future implementation work; this report does not change frontend code.

### P1 — Integrate Screenpipe as optional context

**Process:** query the local API for a bounded time window and attach context references to the matching incident.

**Problem:** broad desktop capture may expose unrelated confidential data, and context records can be mistaken for authoritative security telemetry.

**Solution:** opt-in capture, minimum scope, filters, local-first configuration, provenance labels, and graceful fallback when Screenpipe is offline. Verify the installed version's API and permissions rather than assuming every endpoint behaves identically.

### P1 — Prove event correlation and evidence integrity

**Process:** link KYC events, Guardian decisions, context references, and frontend nodes with stable IDs.

**Problem:** timestamps alone are insufficient to establish causality across services, and a displayed green integrity indicator is meaningless without a defined verification input.

**Solution:** test parent/correlation links, distinguish event time from ingestion time, verify evidence hashes against the original bytes, and include a negative test in which altered evidence must fail verification.

### P1 — Keep narration and rendering non-blocking

**Process:** the graph consumes events independently of optional animation, speech, or context enrichment.

**Problem:** a slow Screenpipe query, GPU frame, or text-to-speech provider could make the interface look frozen or delay security processing if coupled to the same synchronous path.

**Solution:** isolate optional tasks, use bounded timeouts and cancellation, show stale/offline state, and prove that Guardian decisions and event ingestion continue when Screenpipe, audio, or rendering is unavailable.

## 10. Demo acceptance gates

Do not declare the demo competition-ready until these tests have evidence attached:

- [ ] The KYC incident scenario is pinned to a real source commit or explicitly labeled synthetic.
- [ ] The scenario runs only against a local/staging fixture with synthetic data.
- [ ] The attack attempt, Guardian decision, containment result, and replay share stable correlation IDs.
- [ ] The frontend updates while the scenario is running; it does not wait until the final report.
- [ ] Live, simulated, replayed, contextual, inferred, and verified items are visually distinct.
- [ ] A failed or delayed event stream is shown as a telemetry gap.
- [ ] A Screenpipe-disabled run still completes successfully.
- [ ] A Screenpipe query is limited to the relevant context and does not expose unrelated screen/audio content.
- [ ] Altering an evidence artifact causes the integrity check to fail.
- [ ] Filtering or pausing the graph never deletes underlying event history.
- [ ] Audio/TTS failure does not delay the policy decision or incident ingestion.
- [ ] Build, unit, integration, and browser end-to-end test results are recorded with commit IDs and timestamps.
- [ ] No credentials, personal KYC records, or raw runtime logs are committed.

## 11. Sources and current references

1. Frontend repository: https://github.com/vgactech/artcb_TERMINATOR_FRONTEND
2. Frontend design specification commit: https://github.com/vgactech/artcb_TERMINATOR_FRONTEND/commit/88b124bd7c185c42bcafc3448570bb42df321a26
3. KYC repository: https://github.com/vgactech/artcb_kyc
4. ARTCB-TERMINATOR private repository: https://github.com/vgactech/ARTCB-TERMINATOR
5. R045 experiment-branch report: https://github.com/vgactech/ARTCB-TERMINATOR/blob/experiment/artcb-api-mcp-integration/rapports/R045_operational_delta_live_execution_acceptance_gate.md
6. Screenpipe official repository: https://github.com/screenpipe/screenpipe
7. Screenpipe REST API reference: https://docs.screenpi.pe/cli-reference
8. Screenpipe security and privacy: https://screenpipe.com/security
9. Screenpipe license file: https://github.com/screenpipe/screenpipe/blob/main/LICENSE.md

---

## 12. Final audit statement

The recommended path is to first establish a reproducible, controlled KYC scenario, then connect its actual events to Guardian and the frontend, and only then add Screenpipe context as a separately labeled, optional evidence stream. This order prevents a visually convincing demo from overstating what was detected, blocked, or cryptographically verified.

**No application code was changed. No logs were committed. No merge, rebase, or deployment was performed. The ARTCB-TERMINATOR repository's private visibility remains unchanged.**


## 13. Scope clarification and revised competition direction (2026-10-16)

This section refines the original R046 proposal to reflect the latest competition objective. It supplements the findings above; it does not erase unresolved prerequisites or convert unverified functionality into a completed implementation.

### 13.1 Intended outcome

The competition demo should present one coherent, real-time defensive story:

1. The frontend shows a controlled KYC workflow and its normal baseline.
2. A clearly identified attack simulation triggers a reproducible failure pattern in a dedicated test fixture.
3. KYC/test-harness telemetry emits structured events.
4. ARTCB/Guardian consumes the relevant events and produces a traceable defensive decision.
5. The frontend renders the event sequence live, including detection, decision, confirmed containment, evidence and replay.
6. Screenpipe contributes time-bounded operator context from its local memory/search capability, where available and explicitly enabled.
7. The final view distinguishes what was observed, what was decided, what was confirmed, what came from Screenpipe, and what was simulated or inferred.

The intended presentation is a live, time-correlated cyber-incident demonstration. Unless it is run against an authorized live environment with verified telemetry, it must be described as a **controlled real-time simulation**, not as a real external cyberattack. Never attack production KYC systems or third-party infrastructure for a competition demo.

### 13.2 Repository responsibilities and boundaries

The current repository observations remain important:

- **ARTCB-TERMINATOR:** private; this repository is the audit/report coordination point. Its visibility must remain private for the competition team. The present task changes only this report.
- **artcb_TERMINATOR_FRONTEND:** public at the time checked; its visible R001 is a frontend design specification, not proof of a fully implemented or connected interface.
- **artcb_kyc:** public and empty at the time checked; no KYC implementation or reproducible defect can currently be verified from its contents.
- **artcb:** private at the time checked; it is the ARTCB core repository. Its current implementation and data contracts must be inspected before deciding what “replace the blockchain” means technically.

The latest direction mentions working on the frontend, KYC and ARTCB core. That is a multi-repository implementation phase, but R046 itself does not authorize or perform changes in those repositories. Before any code changes, establish a per-repository work plan and explicit file/branch boundaries. Keep ARTCB-TERMINATOR private, do not publish credentials or incident logs, and do not merge or deploy without a separately agreed release step. The public frontend and KYC repositories must contain synthetic demo data only unless their visibility is deliberately reviewed by the owner.

### 13.3 Important correction: Screenpipe memory is not a blockchain replacement on a like-for-like basis

The phrase “replace the blockchain with Screenpipe memory” needs a precise technical definition.

**What Screenpipe can provide:** local-first capture and searchable context, including screen/application information and, when enabled, audio/transcription context. Its documented local API and installation path can make that context available to the demo. See https://screenpipe.com/how-to-install and https://github.com/screenpipe/screenpipe.

**What a blockchain or append-only ledger is commonly intended to provide:** a tamper-evident history, ordered records, and a verification mechanism whose guarantees depend on the actual ledger design and deployment.

These are different functions. Screenpipe memory is useful as a contextual retrieval layer, but it must not be presented as automatically immutable, consensus-backed, cryptographically authenticated, or equivalent to blockchain finality. Search results and captured screen context do not, by themselves, prove that a KYC state transition occurred or that a defensive action succeeded.

**Recommended design for the competition:** replace the blockchain dependency in the demo's *context/memory presentation layer* with Screenpipe-backed searchable context, while retaining a separate evidence-integrity mechanism for security claims. For example, the demo can store normalized incident events and evidence references in an append-only event store or deterministic fixture, hash the exact evidence artifacts, and verify those hashes during replay. If the current ARTCB implementation relies on blockchain-specific guarantees for authorization, consensus, identity, or audit integrity, do not remove that dependency until each guarantee has a documented replacement and corresponding tests.

The implementation decision must therefore be made per responsibility, not by swapping one product name for another:
- Context retrieval and operator memory → Screenpipe adapter.
- KYC state and authoritative business outcome → KYC service/test fixture.
- Detection and policy decision → ARTCB/Guardian service.
- Evidence provenance and integrity → explicit event/evidence contract plus a verified integrity mechanism.
- User-facing visualization and replay → frontend.

### 13.4 Screenpipe integration contract

The frontend should not directly treat arbitrary Screenpipe results as security events. Use a small adapter boundary with these responsibilities:

- Check the local service's health before attempting context retrieval.
- Query only the relevant incident time window and necessary content types.
- Preserve source, capture/query timestamps, result references and available integrity metadata.
- Normalize results into a distinct `context_evidence` type; do not convert them into authoritative KYC or Guardian events.
- Mark the context as unavailable, denied, stale or empty when appropriate.
- Keep the demo functional when Screenpipe is not installed, is stopped, or has no matching result.
- Make capture opt-in and explain the screen/audio scope to the operator; use filters and avoid unrelated personal, identity or secret data.
- Keep Screenpipe access local by default. Any sync, export, cloud transcription or external AI path must be separately configured and disclosed.
- Review the current Screenpipe installation instructions, API behavior, security guidance and license before bundling or redistributing any component.

A useful frontend label is **“Screenpipe context — corroborative, not authoritative.”** This communicates the role without overstating the evidence.

### 13.5 Minimum live-demo wiring

The smallest end-to-end vertical slice should be implemented and verified in this order:

1. **Scenario controller:** starts, stops and resets one deterministic synthetic KYC incident. Each run receives a unique scenario ID.
2. **KYC fixture:** exposes the normal and failure states needed for the scenario, with synthetic identities only.
3. **Event adapter:** maps KYC and test-harness events into a versioned envelope with event ID, scenario ID, correlation ID, source, event time, ingestion time, event type, status and evidence references.
4. **ARTCB/Guardian adapter:** submits or consumes the supported event contract and returns an identifiable policy decision. The actual endpoint and schema must be discovered from source; do not invent an API contract.
5. **Live frontend stream:** updates the timeline and graph as events arrive. Reconnection, duplicate events and out-of-order events must be handled explicitly.
6. **Screenpipe context adapter:** enriches the matching time window independently; timeout or failure must not block the defensive event path.
7. **Evidence inspector and replay:** allows the presenter to inspect source and provenance, replay the incident, and verify the recorded evidence-integrity result.
8. **Demo reset and fallback:** returns to baseline without deleting the saved run evidence; a no-Screenpipe run and a no-camera/no-audio run must still work.

Do not start with visual polish or an elaborate 3D scene if the event path is not proven. The competition-critical proof is the connected incident lifecycle; 3D, gestures, voice and narration are presentation layers that must not control the defensive decision.

### 13.6 Competition acceptance criteria

In addition to Section 10, the following are required before describing the system as wired end-to-end:

- [ ] A single documented command or UI action starts a deterministic demo run.
- [ ] The KYC failure mode is linked to an actual source commit and regression test, or the UI clearly labels it as synthetic.
- [ ] A scenario ID can be followed from KYC through ARTCB/Guardian into the frontend and replay.
- [ ] The UI shows event time and receive time separately and exposes missing/delayed telemetry.
- [ ] The displayed defensive decision is backed by an actual response/event, not by animation.
- [ ] “Blocked” or “contained” appears only after a confirming result or assertion.
- [ ] Screenpipe context is provenance-labeled and cannot overwrite KYC state or Guardian decisions.
- [ ] The demo still runs when Screenpipe is offline or permission is denied.
- [ ] The blockchain-removal decision lists every guarantee being removed and the replacement test for each one.
- [ ] A replay detects tampering in any artifact for which integrity verification is claimed.
- [ ] Public repositories contain no credentials, raw KYC data, personal screen/audio captures or runtime logs.
- [ ] The private visibility of ARTCB-TERMINATOR is checked again after report updates.

### 13.7 Immediate next actions

**P0 — Resolve the KYC source gap.** Populate or identify the authorized KYC implementation, pin its commit, and provide the failing test/expected-vs-actual behavior. Until then, use an explicit synthetic fixture.

**P0 — Map the actual ARTCB integration boundary.** Inspect the existing event, policy and storage contracts in the core repository before deciding which blockchain responsibilities are relevant to this frontend demo. Do not assume that the frontend can safely replace core persistence or authorization.

**P0 — Verify the frontend baseline.** Confirm the actual framework, package scripts, build/test commands, and current Screenpipe-related files. The R001 document alone does not prove those components exist in executable form.

**P1 — Build the incident vertical slice.** Connect one scenario to one real event path, one defensive decision, one live timeline and one replay before expanding to multiple attack types.

**P1 — Add Screenpipe context as an optional adapter.** Validate installation, local service health, query scope, permissions, offline behavior and licensing against the currently installed version.

**P1 — Decide ledger replacement by guarantee.** Produce a short mapping from each blockchain-dependent responsibility to its proposed replacement, threat assumptions and automated acceptance test. Screenpipe memory alone is not an integrity substitute.

**P2 — Add presentation features.** Only after the core flow passes should the team add richer 3D visualization, gesture controls, voice narration and polished pitch choreography.

---

## 14. Updated final audit statement

The clarified competition objective is a connected frontend/KYC/ARTCB defensive incident demonstration, with Screenpipe providing optional searchable operator context in place of blockchain-backed context retrieval where appropriate. It is not technically accurate to claim that Screenpipe memory is a direct substitute for every property a blockchain may provide. Preserve explicit evidence integrity and authoritative KYC/Guardian outcomes independently.

The immediate blockers remain the empty KYC repository and the lack of verified executable frontend integration in the evidence reviewed. The next step is to establish the real KYC reproduction and inspect the actual ARTCB/frontend contracts, then connect the smallest complete vertical slice. Until that work is performed and tested, describe the result as a design and integration plan, not a completed live system.

**This update changes only R046 in the private ARTCB-TERMINATOR repository on the existing experiment branch. It does not change application code, the ARTCB core, the frontend repository, the KYC repository, repository visibility, deployment state, or runtime logs.**
