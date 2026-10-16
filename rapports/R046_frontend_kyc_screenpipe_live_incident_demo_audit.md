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
