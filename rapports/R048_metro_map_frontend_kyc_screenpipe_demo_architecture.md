# R048 — Metro-Map Architecture, Frontend Scope, KYC Import Gate, and Screenpipe Incident Demonstration

**Date:** 16 October 2026  
**Status:** Architecture and repository-state audit; no application code changed  
**Target repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `experiment/artcb-api-mcp-integration`  
**Report path:** `rapports/R048_metro_map_frontend_kyc_screenpipe_demo_architecture.md`

## 1. Executive decision

Use the Paris Metro / rail-network metaphor as the architectural map for ARTCB TERMINATOR, but implement it as a typed dependency graph rather than a decorative diagram. Metro lines represent independently deployable or independently testable modules; stations represent functions, sub-functions, services, state transitions, and validation gates; interchanges represent explicit contracts between modules. A line must not silently depend on another line's internal implementation.

The competition demo should tell one deterministic defensive-security story: a synthetic KYC workflow encounters a controlled failure during a simulated cyber incident; the frontend renders the event stream and dependency graph in real time; the defensive component detects and responds; and Screenpipe supplies optional operator-context evidence when available. The UI must distinguish simulated events, observed telemetry, detections, confirmed outcomes, and unknowns.

The KYC source import remains blocked pending explicit permission or a license that permits copying and redistribution. The source repository is public but currently exposes no license file or license metadata in the inspected repository state. Do not copy its entire history or contents into `vgactech/artcb_kyc` until this is resolved. This does not block frontend progress: use synthetic fixtures and a narrow adapter contract.

## 2. Expertise activated

- Modular software architecture and graph-based dependency modeling.
- Frontend architecture, event-driven UI, and real-time visualization.
- Defensive cybersecurity and controlled incident simulation.
- KYC workflow modeling, synthetic test data, and privacy engineering.
- GitHub governance, software provenance, and licensing diligence.
- Screenpipe integration, operator-context retrieval, and data minimization.
- Event schemas, observability, incident replay, and evidence integrity.
- Competition demo design and claim verification.

## 3. Repository state checked on 16 October 2026

| Repository | Observed state | Audit consequence |
|---|---|---|
| `vgactech/ARTCB-TERMINATOR` | Private; default branch `main`; experimental branch `experiment/artcb-api-mcp-integration` exists; connected account has push/admin rights | Keep the coordination repository private. This change is report-only. |
| `vgactech/artcb_kyc` | Public; default branch `main`; size 0 KB; connected account has push/admin rights | Destination is empty. No import was performed. |
| `lynadatacraft/atelier-model-thinking-kyc` | Public; default branch `main`; reported size approximately 91,503 KB; connected account has pull but not push rights; README is minimal; no `LICENSE` file found at the repository root | Full mirroring is not cleared for reuse. Public visibility alone does not grant republication rights. |
| `vgactech/artcb_TERMINATOR_FRONTEND` | Public; default branch `main`; the root tree returned only a `rapports/` directory; earlier inspection found a frontend design specification, not a working integration | Do not describe the live frontend or Screenpipe integration as implemented until executable evidence is available. |
| `vgactech/artcb` | Previously identified as private; protected core repository | No changes to this repository are in scope. |

The API's returned source tree is not a complete, verified inventory of all files. No source import, deployment, log upload, secret modification, or application-code change was performed.

## 4. The metro-map model: process, problem, and solution

### 4.1 Process

Represent the architecture as a graph with four primary concepts:

- **Line / module:** a bounded subsystem with a clear responsibility, owner, version, and test suite.
- **Station / function:** an operation or state transition exposed by a module.
- **Interchange / contract:** a documented interface through which two modules exchange events or data.
- **Track / dependency:** a typed relationship such as calls, emits, consumes, authorizes, stores, observes, or verifies.

Each station should have a stable identifier, input/output schema, failure states, timeout policy, provenance fields, and acceptance tests. The graph should support multiple routes and branches, because real execution is not always linear.

### 4.2 Problem

A visual metro analogy can become misleading if it only illustrates a desired architecture. It does not prove that the code implements the displayed route, that modules are isolated, or that an event actually traversed a given station. A line can also become a hidden monolith if it reaches directly into another module's private state.

### 4.3 Solution

Maintain two linked but distinct graphs:

1. **Design graph:** the intended architecture, module boundaries, interfaces, and allowed dependencies.
2. **Runtime graph:** actual events and calls observed during an execution, correlated by trace and event identifiers.

A UI overlay must never imply that a runtime path was executed merely because that path exists in the design graph. Show design-only paths as planned, runtime paths as observed, and gaps as uninstrumented or unknown.

### 4.4 Suggested module lines

These are proposed logical lines, not claims that the modules already exist in the frontend repository:

1. **Experience Line:** user input, incident timeline, metro-map canvas, accessibility, and operator controls.
2. **Orchestration Line:** scenario lifecycle, agent/tool dispatch, correlation, and workflow state.
3. **KYC Line:** synthetic KYC case, validation steps, decision contract, and explicit failure injection for the demo.
4. **Guardian / Defense Line:** detection, policy evaluation, containment decision, and response status.
5. **Evidence Line:** event normalization, timestamps, hashes, signatures where available, provenance, and replay.
6. **Screenpipe Context Line:** optional capture/search context, source metadata, operator consent, and privacy filtering.
7. **Adapter / Integration Line:** versioned contracts between frontend and backend, with timeouts, retries, and schema validation.
8. **Test / Simulation Line:** deterministic fixtures, attack simulation controls, expected event sequences, and acceptance tests.

These lines should be split further only when the split creates an independently testable boundary. Avoid creating a separate module for every function if that introduces unnecessary inter-service dependencies.

## 5. Canonical station and event contract

Every runtime station should emit a normalized event with, at minimum:

- `event_id`, `trace_id`, and optional `parent_event_id`;
- `occurred_at` and `received_at`, including clock/source metadata where available;
- `source_component`, `module_line`, `station_id`, and `component_version`;
- `event_type`, `status`, and an explicit evidence classification;
- references to input/output artifacts, preferably by content hash where suitable;
- `simulation=true|false` and `observed=true|false` as distinct fields;
- `confidence` or severity only where the producing subsystem defines its meaning;
- privacy classification and retention policy;
- integrity metadata, when actually generated and verified.

Do not claim nanosecond accuracy merely because timestamps contain nine decimal places. Record the precision and clock source actually supplied by the producer. Do not place raw identity documents, secrets, access tokens, or unrestricted screen captures into the shared event stream.

## 6. KYC source import gate

### Process

A Git clone preserves a repository's commit history. Importing that history into another repository is a separate publication action and should record the source URL, resolved commit SHA, import method, checksums, exclusions, and attribution.

### Problem

The source repository is public and substantial, but the inspected state has no root `LICENSE` file or license metadata. The connected account has read-only access to the source. The target `artcb_kyc` is empty, but emptiness does not itself authorize copying another party's repository. The source may also contain datasets or documents whose privacy and redistribution status require separate review.

### Solution

Before importing:
1. Obtain written permission from the source owner or confirm a license that allows the intended copy and redistribution.
2. Resolve and record an exact source commit SHA.
3. Generate a complete inventory and identify large files, personal data, secrets, and non-redistributable materials.
4. Preserve upstream notices and attribution; do not invent a license.
5. Create a provenance manifest with source URL, commit, timestamp, file counts, checksums, and exclusions.
6. Run secret scanning and data-classification checks before pushing any authorized import.

Until then, implement against a small synthetic fixture with no real identity data. The fixture must be labelled synthetic in both the event payload and the UI.

## 7. Screenpipe integration boundary

Screenpipe should be an optional context provider, not the authority that decides whether a KYC case is valid or an attack is confirmed.

**Proposed flow:** operator enables capture/context retrieval → Screenpipe returns a relevant item and source metadata → a privacy filter applies scope and redaction → an adapter emits a context-reference event → the frontend links that reference to the incident timeline.

Required controls:
- make capture status visible and provide a clear operator-controlled enable/disable path;
- minimize collection and avoid ingesting unrelated personal content;
- keep secrets, credentials, identity documents, and unrelated screen content out of the demo evidence stream;
- show source, capture/retrieval time, and limitations for each returned context item;
- handle Screenpipe unavailable, delayed, or empty results without blocking detection or containment;
- never represent retrieved context as proof of an attack unless independent evidence supports that conclusion.

The current repository inspection does not prove that Screenpipe is wired into the frontend. This must be demonstrated through code inspection and a live integration test before claiming completion.

## 8. Controlled incident demo: expected end-to-end route

Use a deterministic scenario with synthetic data:

1. **Input station:** operator starts a labelled simulation.
2. **KYC intake station:** a synthetic case enters the workflow.
3. **Failure station:** inject one predefined anomaly, such as a mismatch between an expected decision state and the observed synthetic event.
4. **Detection station:** the defensive component emits a detection with its rule/version and evidence references.
5. **Response station:** a controlled response is recorded; the UI distinguishes proposed, executed, and verified actions.
6. **Screenpipe context station:** optional context is attached if available; failure to retrieve context does not halt the incident.
7. **Evidence station:** preserve event order, parent-child links, source metadata, and integrity results.
8. **Replay station:** operator can replay the incident and inspect why each state changed.
9. **Closure station:** the scenario ends only after the expected checks have passed or are explicitly marked inconclusive.

Do not use a real third-party target or perform destructive actions. The demonstration should simulate the incident and validate defensive handling in an environment controlled by the project team.

## 9. Frontend acceptance criteria

The frontend should not be declared integrated until all of the following are demonstrated:

- A real browser session receives a sequence of events from the intended backend or test adapter.
- The metro map distinguishes design paths from runtime-observed paths.
- Events appear incrementally with a measured latency, and historical events remain available.
- Parallel branches and parent-child relationships are preserved.
- The UI distinguishes simulated, observed, detected, confirmed, blocked, failed, and unknown states.
- Missing telemetry is visible as a gap, not misrepresented as proof of no activity.
- Screenpipe can be unavailable without delaying or suppressing the defensive response.
- The operator can inspect a station, trace its upstream causes, follow downstream effects, and replay the event sequence.
- The UI does not expose raw personal data, credentials, or secret-bearing logs.
- Automated tests cover valid sequences, malformed events, duplicate delivery, late arrival, disconnect/reconnect, and Screenpipe failure.
- The demo's final claims match evidence collected during the actual run.

## 10. Priority order

**P0 — Now**
- Keep `ARTCB-TERMINATOR` private.
- Keep this work report-only in that repository.
- Build the demo contract and synthetic KYC fixture in the explicitly authorized implementation repository.
- Request permission/license clarification for the KYC source.

**P1 — Next**
- Inventory the frontend repository and identify its actual build/run path.
- Implement the metro-map visualization against the canonical event contract.
- Add an adapter for Screenpipe with consent, minimization, and failure isolation.
- Demonstrate one complete simulated incident in a browser.

**P2 — Before the competition demo**
- Capture a reproducible test run and verify event ordering, evidence references, and failure behavior.
- Record which integrations are live, simulated, or unavailable.
- Rehearse the operator walkthrough and ensure every claim can be substantiated from the captured run.

## 11. Scope and change control

This commit adds this report only to `rapports/` in `vgactech/ARTCB-TERMINATOR`. It does not modify `vgactech/artcb`, the frontend, `artcb_kyc`, the source KYC repository, VLC&ARTCB, application code, runtime configuration, secrets, or logs. No merge, deployment, or import was performed.

## 12. Final assessment

The metro-map concept is a useful architectural foundation if it becomes a versioned design graph linked to a separately evidenced runtime graph. The fastest safe route to the competition demo is not to wait for an unlicensed bulk import: it is to establish a synthetic KYC contract, connect the event stream to the frontend, isolate optional Screenpipe context, and demonstrate a complete defensive incident with honest evidence labels. The source import can follow as soon as the rights, provenance, and data-safety gates are satisfied.
