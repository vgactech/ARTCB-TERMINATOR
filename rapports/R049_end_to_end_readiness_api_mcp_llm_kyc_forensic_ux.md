# R049 — End-to-End Readiness Audit: Runtime Separation, API/MCP Proof, LLM/KYC Certification, and Forensic Operator UX

**Date:** 2026-10-11  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `feat/artcb-forensic-integration`  
**Baseline synchronized:** `main` at `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`  
**Related report:** R048 — Live Node Certification & Open Items Triage  
**Change scope:** this report only, under `rapports/`  
**Status:** NOT CERTIFIED for full end-to-end live operation; no merge authorized

---

## 1. Executive decision

**The available evidence does not establish that the two ARTCB-TERMINATOR AWS environments are both provisioned, running, connected to one another, or executing the full live scenario.** R048 certifies three *ARTCB blockchain* nodes (N2, N3, N4) at the recorded verification time. It explicitly distinguishes those nodes from the separate ARTCB-TERMINATOR hackathon infrastructure and lists the hackathon EC2 environments as awaiting organiser provisioning. The three-node ARTCB result must not be used as proof that two TERMINATOR AWS servers are operational.

The integration branch contains an HTTP-only ARTCB bridge, a forensic panel, phase definitions, and API status wiring. These are implementation artifacts, not proof that the remote API/MCP endpoint is reachable or that an operation was executed remotely. R048 says the configured `ARTCB_API_URL` was corrected to N4, but the bridge status still required a Guardian backend restart and a fresh retest. The code path currently attempts JSON-RPC requests at `/mcp`; that exact endpoint, authentication behavior, protocol compatibility, and the response from the live service must be demonstrated before claiming successful mediation.

The repositories `vgactech/artcb_API` and `vgactech/artcb_MPC` currently return GitHub's **empty repository** response in the inspected account context. They therefore do not presently demonstrate that the ARTCB API or MCP source has been copied or published into those repositories. The primary `vgactech/artcb` repository does contain the ARTCB API application and has commit history referencing MCP functionality. Keep the source of truth there; consume it across a documented network contract. Do not copy ARTCB source into TERMINATOR or alter the separate ARTCB repository as part of this report.

Other critical claims remain unproven: current inference for every local/cloud LLM, actual ARTCB-mediated model calls, a complete authorized KYC run, and browser-to-backend forensic visualization and audio through a full incident lifecycle. R048 still records OpenAI quota exhaustion, an invalid/expired ElevenLabs key, a missing jury frontend origin, a stalled PBFT public tip, and an unverified post-restart MCP bridge.

**Decision:** retain the feature branch as an isolated experiment. Do not merge it into `main` until the owner explicitly approves after reviewing fresh evidence and the full diff.

## 2. Expertise activated

- Distributed infrastructure and environment separation.
- Git branch provenance and non-destructive repository review.
- API/MCP protocol interoperability and HTTP service diagnostics.
- LLM runtime inventory, provider authentication, quota handling, and execution-path provenance.
- KYC workflow assurance, fixture governance, and evidence provenance.
- Cryptographic event integrity and independent tamper verification.
- Browser event streaming, forensic graph state, and real-time observability.
- Audio UX, asynchronous narration, prerecorded alerts, and accessibility.
- Operational readiness, failure injection, and acceptance-test design.

## 3. Repository synchronization and source boundaries

The current GitHub comparison reports `feat/artcb-forensic-integration` is **five commits ahead of `main` and zero commits behind**. The current `main` baseline observed during this review is `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`. The feature branch contains the forensic integration and R046–R048 reports.

The ARTCB primary repository's latest commit returned by the connector is `7304d493018995d851ed5c13107c5e9d5bd79268` (R590 positioning report). The API/MCP split repositories were checked independently:
- `vgactech/artcb_API`: GitHub reports the repository is empty.
- `vgactech/artcb_MPC`: GitHub reports the repository is empty.
- `vgactech/artcb`: non-empty primary repository with the API application and MCP-related commit history.

This is a repository-state observation, not proof that no unpushed local files exist elsewhere. It does mean the two split repositories cannot currently be treated as published, independently verifiable implementations.

**Boundary rule:** keep all ARTCB source in `vgactech/artcb`. TERMINATOR may use only the versioned API/MCP interface. Do not vendor, copy, submodule, subtree, or otherwise transplant ARTCB source into this repository. This report does not modify the ARTCB, API, or MCP repositories.

## 4. Distinguish the two infrastructure estates

### 4.1 ARTCB blockchain nodes

R048 reports a live verification of:
- N2/OVH2: `status=ok`, height 1142, SHA prefix `5be65d9f`, integrity and PQC reported active.
- N3/AWS3: `status=ok`, height 1142, same SHA prefix, integrity and PQC reported active.
- N4/OVH4: `status=ok`, height 1142, same SHA prefix, integrity and PQC reported active.
- N1/OVH1: retired/offline; port 8000 closed.

This is positive evidence for the ARTCB blockchain nodes at the time and using the methods stated in R048. It is not a current re-probe performed by this report, and it does not certify the TERMINATOR AWS hosts.

### 4.2 ARTCB-TERMINATOR hackathon runtime

R048 lists the two hackathon EC2 servers as awaiting organiser provisioning. No evidence in R048 demonstrates both TERMINATOR AWS hosts running, mutually connected, or serving the frontend/backend in the same end-to-end test.

**Required distinction in all status displays and reports:** `ARTCB blockchain node health` and `ARTCB-TERMINATOR deployment health` are separate dimensions. A green ARTCB chain node must never imply that the TERMINATOR attack/defense demo is live.

### 4.3 PC-local execution

The desired behavior—use the local PC when it is detected and otherwise distribute work across the intended AWS hosts—is not yet proven by the reviewed evidence. A host must be reported as available only after a fresh heartbeat and a harmless capability probe. Do not infer PC presence from a saved configuration or from a browser being open.

Recommended host states: `online-and-probed`, `online-but-unprobed`, `offline`, `unauthorized`, and `unknown`. The scheduler must record which host actually executed each task, with a run ID and timestamp.

## 5. API/MCP integration: code exists, live mediation is not certified

### Process

The branch's `guardian_mcp/artcb_bridge.py` creates JSON-RPC 2.0 requests for MCP methods such as `initialize`, `tools/list`, and `tools/call`, targeting `ARTCB_API_URL/mcp`. It adds a correlation ID to tool calls and optionally adds a Bearer token and agent ID header. The Guardian API exposes `GET /api/artcb/status`.

### Problem

The existence of this adapter does not establish that the target service supports this exact HTTP MCP route or protocol version. R048 states that the status endpoint was still `available=false` and required a Guardian backend restart after the URL correction. The inspected bridge code does not independently prove that a successful remote tool call occurred. In addition, the current documented base URL is plain HTTP, so remote use must not be called secure transport unless the deployment boundary supplies a separately verified protected channel.

The `health()` path also needs a protocol-level acceptance check: a reachable HTTP endpoint is insufficient if MCP initialization or tool discovery returns an error, an empty tool list, an incompatible schema, or a server identity/version different from the expected service.

### Required acceptance test

1. Restart the Guardian backend in the intended environment so it receives the corrected Doppler value; do not expose or copy secrets into the repository.
2. Call `/api/artcb/status` from the actual running backend and preserve the sanitized JSON response and timestamp.
3. Verify `available=true`, expected server identity/version, a non-empty tool inventory, and a known protocol version.
4. Execute one harmless, read-only MCP capability using synthetic input and a unique correlation ID.
5. Confirm the matching request on the ARTCB service side and correlate the response with the TERMINATOR event. A client-generated correlation ID alone is not remote-side proof.
6. Validate response schema, authentication behavior, timeout, unavailable service, invalid credentials, and malformed JSON-RPC response.
7. Confirm the Guardian policy path still operates when ARTCB is unavailable and that no failed remote call is labelled as an ARTCB success.
8. Record the exact route as `artcb-mcp`, `artcb-api`, or `direct-provider`; never conflate these paths.

**Exit gate:** a synthetic transaction is independently observable on both sides, correlated, schema-valid, and successful; negative-path tests correctly report failure. Until then, label the integration `implemented; live remote mediation not certified`.

## 6. LLM inventory and proof of the actual call path

### Process

Each intended model must be tested as an individual execution target. The allowed route classes are:
- `local-direct`: TERMINATOR invokes a model runtime on the local PC.
- `provider-direct`: TERMINATOR invokes an external model provider directly.
- `artcb-api`: TERMINATOR invokes the documented ARTCB API.
- `artcb-mcp`: TERMINATOR invokes a declared MCP capability served by ARTCB.

### Problem

The reviewed reports do not provide a complete current model inventory with successful per-model inference evidence. R048 records OpenAI `gpt-4o` blocked by exhausted quota. The ElevenLabs credential is recorded as HTTP 401, which blocks the current voice-provider path. Neither configured credentials nor installed packages establish that a model is callable. A response generated through a direct provider call does not prove that ARTCB mediated it.

### Required inventory fields

For each intended local model/provider, record:
- provider, model ID, and revision where available;
- host/runtime identity and installation status;
- reachability and authentication result;
- harmless synthetic smoke-test result and timestamp;
- request/run/correlation ID, latency, response status, and timeout;
- quota/rate-limit state where available;
- actual route class and evidence supporting it;
- fallback taken, if any, with the fallback explicitly named.

Never record API keys, authorization headers, private credentials, or raw secrets in the report or logs.

### Acceptance gate

Run one harmless smoke test for every intended model/provider. For an ARTCB-mediated call, require both the TERMINATOR-side event and corresponding ARTCB-side evidence. Classify each model as `verified`, `failed`, `not configured`, or `not tested`. Do not declare “all local and API LLMs operational” until all intended entries are verified.

## 7. KYC: prior pipeline evidence is not live end-to-end certification

### Process

The ARTCB repository documents a KYC pipeline and R046 reports the chain build identifier associated with a prior KYC-pipeline change. Earlier TERMINATOR reports also describe an offline example-form run.

### Problem

A code path, an old offline run, or a passing subset of tests does not prove that the current deployed TERMINATOR runtime can call the intended ARTCB capability and complete an authorized KYC workflow. The reviewed reports do not provide a current, correlated TERMINATOR-to-ARTCB KYC execution. R045/R044 also record a KYC test mismatch in prior evidence; R048 does not say that this mismatch has been resolved.

### Required acceptance test

1. Use synthetic or explicitly authorized fixtures only; do not place personal KYC documents in the report or ordinary logs.
2. Record fixture version/hash, pipeline/rule/model version, stage IDs, timestamps, and sanitized results.
3. Exercise every required stage and validate schema, missing/conflicting evidence, non-applicable fields, protected-zone outcomes, false positives, and unavailable external screening sources.
4. Verify data-source version and freshness where sanctions or other external screening is used.
5. If called through API/MCP, correlate the TERMINATOR request with the ARTCB-side execution and stage outcomes.
6. Separate labels for `offline fixture test`, `remote integration test`, and `authorized live case`.
7. Ensure failures and unknowns remain visible and cannot be represented as a completed KYC decision.

**Exit gate:** all required tests pass or have an explicitly approved exception; a synthetic end-to-end run is correlated across both services; evidence provenance and data freshness are recorded. Do not claim real-world KYC is validated before this gate passes.

## 8. Forensic graph, progress values, and voice: code-level gaps

### 8.1 Process and current implementation

The feature branch defines forensic phases and a `ForensicPanel`. The phase configuration includes numeric detection, block, and resolution percentages and narration text. The helper `phaseFromAgentIndex()` advances through intermediate phases based on an agent index. `speakPhaseAlert()` posts narration text to `/api/llm-attack/stream?voice=true&speed=1.1` with a three-second timeout.

### 8.2 Problems

- The percentages in the phase table are fixed per phase; they are not computed from measured detection, containment, remediation, or verification evidence. They can therefore be mistaken for real progress.
- `phaseFromAgentIndex()` maps an index to intermediate phases. That is an animation/progression cue, not independent proof that a corresponding security event occurred.
- The current voice helper invokes a network streaming endpoint. It does not implement a library of prerecorded audio assets as requested, and a call to an attack-stream endpoint must not be assumed to be equivalent to a dedicated TTS-only route.
- Phase text currently contains assertions such as “tool not executed”, “chain integrity confirmed”, and “incident closed”. These statements must only be spoken after the authoritative executor and verification results confirm them.
- R048 records the ElevenLabs credential as invalid/expired, so current dynamic voice playback is blocked by an external dependency.

### 8.3 Required design

Use a canonical event stream as the sole authority for phase transitions. Agent index or animation may show presentation progress but must not set security status. Keep the complete event history even when the UI filters or summarizes it.

Use separate, evidence-backed metrics:
- scenario stages completed / planned;
- detection status and detector evidence;
- authoritative policy outcome (ALLOW/BLOCK/ESCALATE/UNKNOWN);
- containment actions verified / required;
- remediation checks passed / required;
- integrity checks passed / applicable;
- telemetry sources reporting / expected.

Every percentage must expose its numerator, denominator, and source. Unknown, failed, skipped, and unavailable stages must not be counted as successful.

For audio, prefer reviewed prerecorded clips for fixed critical events. Trigger each clip only from a canonical, confirmed state transition. Keep dynamic TTS optional and asynchronous. Audio must not delay enforcement, mutate incident status, or be the only means of communicating an alert. Show visible text when audio is unavailable.

Use concise tactical summaries with the fixed fields **Observed / Confirmed / Blocked or allowed / Unresolved / Suggested next action**. Tie each summary to a run ID and time window. A suggestion must never be described as an executed action.

### Acceptance gate

Browser E2E tests must prove that real API events update the graph, status labels correspond to authoritative outcomes, percentages are evidence-backed, and audio follows confirmed transitions. With audio disabled or delayed, the security decision path and measured enforcement latency must remain unchanged.

## 9. Open blockers and dependencies

| Priority | Item | Current evidence | Required action |
|---|---|---|---|
| P0 | Two TERMINATOR AWS environments | R048 says hackathon EC2 provisioning is pending | Obtain organiser provisioning/access and prove each runtime with health checks |
| P0 | OpenAI `gpt-4o` | R048: quota exhausted | Account owner restores quota or approves a test provider; rerun the live scenario |
| P0 | Voice provider | R048: ElevenLabs HTTP 401 | Rotate/restore credential through the secret manager; test playback independently |
| P0 | ARTCB bridge live call | R048: status unavailable; restart/retest pending | Restart backend, validate MCP protocol/tool inventory, complete correlated round trip |
| P0 | KYC end-to-end evidence | No current correlated live run in reviewed evidence | Run synthetic end-to-end test and resolve previous test mismatch in the owning repository's workflow |
| P1 | Local PC detection and task routing | Not demonstrated by reviewed evidence | Implement/test heartbeat plus harmless capability probe and actual-host execution attribution |
| P1 | LLM inventory | No complete current per-model smoke-test matrix | Enumerate all intended models and test individually |
| P1 | PBFT public-tip stall | R048: approximately 26-day stall; view-change pending | Recover access and validate consensus/view-change separately from TERMINATOR |
| P1 | `GUARDIAN_FRONTEND_ORIGIN` | R048: empty, jury URL pending | Set only after the authoritative URL is supplied |
| P1 | Branch merge | R048: pending explicit approval | Keep branch isolated; no merge without explicit approval |

External dependencies must remain labelled blocked. Do not convert a credential/quota issue, missing organiser URL, unavailable endpoint, or unprovisioned host into a software PASS.

## 10. Questions that must be answered before certification

1. Are both intended TERMINATOR AWS instances actually provisioned by the organisers, and what authenticated health response proves each is running?
2. What exact host executes each stage: local PC, AWS instance A, AWS instance B, or ARTCB blockchain node?
3. Is the local PC detected through a fresh heartbeat and capability probe, or merely inferred from configuration?
4. What is the live ARTCB API/MCP endpoint contract, including protocol version, tool inventory, authentication, and supported operations?
5. Does the deployed ARTCB service actually expose the `/mcp` route used by the bridge?
6. Can a synthetic read-only request be correlated in both TERMINATOR and ARTCB service-side telemetry?
7. Which local LLMs are installed and which have passed current inference tests?
8. Which external providers are authenticated, funded, and callable today?
9. Which model calls are demonstrably mediated by ARTCB rather than routed directly to a provider?
10. Has the KYC test mismatch been resolved, and is there a current synthetic end-to-end execution with provenance?
11. Which evidence supports every detection, block, containment, resolution, and integrity percentage shown in the frontend?
12. Which prerecorded clip maps to each confirmed event, and what is the fallback if the audio file or browser playback is unavailable?
13. What exact checks must pass before the interface may announce “blocked”, “contained”, or “resolved”?
14. What is the rollback/degraded-mode behavior when the ARTCB service, a local model, a provider API, or one host becomes unavailable?
15. Who will explicitly approve the final merge after reviewing the complete diff and evidence package?

## 11. Required sequence and final verdict

1. Confirm the actual TERMINATOR host inventory and distinguish it from ARTCB blockchain nodes.
2. Obtain the two hackathon runtime environments and prove health, authentication, and host identity.
3. Restart the backend with the corrected endpoint configuration and complete a correlated read-only API/MCP round trip.
4. Build the complete local/API model inventory and verify each model's actual execution path.
5. Resolve the KYC test mismatch through its owning repository workflow and run a synthetic end-to-end KYC test.
6. Replace phase-index-derived security claims and hard-coded percentages with canonical-event and evidence-backed state.
7. Implement/test prerecorded critical audio cues, asynchronous delivery, concise summaries, and browser reconnect/failure behavior.
8. Run cross-host, browser E2E, timeout, quota, authentication, and service-unavailable tests.
9. Review the full feature-branch diff and obtain explicit owner approval before any merge.

**Final verdict: NOT CERTIFIED for full live end-to-end operation.** R048 is useful evidence that three ARTCB blockchain nodes were live and aligned at the recorded check, but it does not certify the two TERMINATOR AWS servers, live API/MCP mediation, all LLMs, real-world KYC, or the complete frontend/voice experience. The bridge and forensic UI exist on the feature branch; the live execution path and the evidence-driven UX still require acceptance tests.

**Change record:** this commit adds this report only under `rapports/` on `feat/artcb-forensic-integration`. No application source, tests, deployment configuration, secret, runtime, log, or external ARTCB repository is changed. No merge, rebase, deployment, or release promotion is performed or authorized.
