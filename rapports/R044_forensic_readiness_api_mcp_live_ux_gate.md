# R044 — Forensic Readiness, ARTCB API/MCP Integration Gate, and Live Operator UX

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `experiment/artcb-api-mcp-integration`  
**Main HEAD observed during review:** `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`  
**Predecessors:** R042 — ARTCB API/MCP Integration Experiment and Real-Time Defensive Operator UX; R043 — ARTCB API/MCP Repository Verification and Safe Integration Gate  
**Status:** REPORT ONLY / NO IMPLEMENTATION / NO MERGE AUTHORIZATION

---

## 1. Executive decision

**Decision: continue the isolated experiment, but do not claim that the two-server architecture, all LLM providers, or a real-world KYC flow are operationally certified.**

The current evidence supports a working Guardian demonstration path for a limited set of scenarios, a documented ARTCB KYC pipeline, and a separately maintained ARTCB API/MCP implementation. It does not establish end-to-end live operation across a local PC and AWS, a reachable ARTCB remote service, complete local-model installation, or successful live LLM attack generation.

The integration branch exists, but the branch comparison reports that it has diverged from current `main`: three commits ahead and four behind at the time of review. The branch contains the R042 and R043 design/review reports; the inspected `guardian_api/app.py` content on the branch matches the main version for the reviewed opening section. **This is not evidence that an ARTCB API/MCP adapter has been implemented.** The branch must not be merged merely because the design reports exist.

This report changes no application source, tests, deployment configuration, credentials, or files in the separate ARTCB repository. No runtime logs or secret values are included. No merge, release promotion, rebase, or integration into `main` is authorized.

## 2. Expertise activated

- Distributed systems and local/cloud topology validation.
- API/MCP contract design and service interoperability.
- LLM runtime inventory, provider failure modes, and model provenance.
- KYC workflow assurance and evidence-based test interpretation.
- Defensive agent orchestration and Guardian enforcement.
- Cryptographic provenance, event ledgers, and forensic reconstruction.
- Real-time event visualization, progress semantics, and observability.
- Voice UX, prerecorded audio cues, asynchronous TTS, and accessibility.
- Reliability engineering, failure isolation, and degraded-mode design.
- Git branch governance and non-destructive repository audit.

## 3. Repository and branch facts

### 3.1 Main branch

The latest main commit identified by the GitHub connector during this review is `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`, whose message identifies the R043 operational-readiness report.

### 3.2 Experiment branch

The existing branch is `experiment/artcb-api-mcp-integration`. The comparison against main reports:

- Status: diverged.
- Experiment branch: three commits ahead of main.
- Experiment branch: four commits behind main.
- The branch has the R042 architecture/UX report and the R043 API/MCP repository verification report.

The divergence matters because reports and assumptions on the experiment branch may predate the latest operational-readiness evidence. Do not merge or silently rebase it. Before implementation, reconcile the branch against the current main deliberately, preserving the experiment's report history and reviewing every resulting diff. The owner must explicitly approve any merge to main.

### 3.3 Scope boundary

All ARTCB capabilities must be consumed through a documented, versioned API and/or MCP boundary. Do not copy, vendor, submodule, subtree, or transplant ARTCB implementation source into TERMINATOR. Do not modify the separate `vgactech/artcb` repository as part of this work. The only permitted repository change for this audit is this report under `rapports/`.

## 4. Operational truth table

| Claim | Evidence currently available | Verdict |
|---|---|---|
| Guardian can return an ALLOW decision for the documented safe-read scenario | R043 reports an observed run | Demonstrated for that scenario; not a universal production guarantee |
| Guardian can BLOCK the documented exfiltration and prompt-injection scenarios | R043 reports observed runs with `tool_was_executed=false` and evidence IDs | Demonstrated for those scenarios; broader coverage remains unproven |
| Guardian's recorded event-chain check passed in those runs | R043 reports PASS for the recorded defender chain | Narrowly demonstrated; not proof of global cross-agent completeness |
| The separate tamper-verification check is correct | R043 reports a genesis-hash lookup mismatch and FAIL | **Not demonstrated; known defect remains open** |
| Both local and AWS TERMINATOR servers are currently live and connected | R043 states the AWS competition servers were not provisioned under the inspected role and the remote OVH endpoint timed out | **Not demonstrated** |
| ARTCB API is reachable from TERMINATOR | R043 reports OVH timeout and Windows startup blocked by `fcntl` | **Not demonstrated** |
| All local LLMs are installed and callable | No complete runtime inventory, model list, or per-model smoke-test evidence is present in the reviewed reports | **Unknown** |
| All API LLM providers are configured and working | OpenAI `gpt-4o` call failed with `credit_balance_exhausted`; other providers are not exhaustively tested | **Not demonstrated** |
| The live LLM attack was intercepted end to end | The reported OpenAI quota failure prevented generation | **Not demonstrated** |
| The KYC pipeline exists and has processed example forms | R043 documents a 12-stage pipeline and an earlier five-form run | Demonstrated as a documented prior run; current runtime not re-executed in this audit |
| KYC is fully validated in a real operational environment | One of seven reported tests fails; production identity, evidence, sanctions-data freshness, and end-to-end live service proof are absent | **Not certified** |
| The browser consumes the real-time stream and plays voice end to end | R041 reports no frontend changes in the R040 backend commit and no independent browser E2E proof | **Not demonstrated** |
| ARTCB API/MCP integration is implemented on the experiment branch | Reviewed branch content and comparison show design/review reports, not an adapter implementation | **Not implemented by the reviewed commits** |

## 5. What "two servers working together" must mean

### Process

A genuine two-environment architecture requires a local TERMINATOR process and a reachable remote service, each with a known identity, build/version, health state, and communication path. Requests need correlation IDs so an operator can prove which side executed each operation.

### Problem

Two local checkouts, two server configurations, a valid temporary AWS identity, or a successful unit test do not prove that two deployed processes are communicating. The previous evidence explicitly reports an unreachable OVH service and no competition EC2 instances visible to the inspected read-only AWS role. The competition environment may be managed by the organisers, so absence from this role is not proof that no organiser-owned server exists.

### Required validation

1. Record each endpoint's owner, environment, version/build identifier, health response, and authentication mode. Never include tokens or credentials in the report.
2. Run an authenticated health check from the actual TERMINATOR host to the actual ARTCB endpoint.
3. Execute one harmless read-only request with synthetic data and verify the remote request ID, provider identity, response schema, and corresponding TERMINATOR correlation event.
4. Exercise timeout, refused connection, invalid credentials, incompatible schema, and remote-service restart cases.
5. Verify that remote unavailability does not silently turn a failed ARTCB call into a claimed success, and that the existing Guardian policy remains active.
6. Run a cross-host test from the actual AWS competition environment only after the organisers provide the endpoint and authorized access.
7. Keep local-only, remote-only, and cross-host results as distinct evidence categories.

**Acceptance criterion:** one synthetic transaction is traced from local intake through the authenticated remote API/MCP call and back, with matching correlation IDs, verified response schema, measured latency, and explicit error handling. Until then, label the architecture "multi-environment design; cross-host operation not certified."

## 6. LLM inventory and proof that ARTCB is actually used

### Process

A model may be local (for example, served by a local runtime) or remote through a provider API. TERMINATOR can call a model directly, or a model operation can pass through an ARTCB API/MCP capability. These paths are not equivalent.

### Problem

A configured API key, installed SDK, model name in configuration, or a successful generic LLM call does not prove that ARTCB API/MCP mediated the call. Likewise, a model listed in a local runtime does not prove that TERMINATOR can invoke it successfully.

### Required inventory

For every model/provider, record only non-secret metadata:

- provider and execution mode: local, remote API, or ARTCB-mediated;
- model identifier and immutable version/revision where available;
- runtime/service endpoint identifier (never credentials);
- whether the process is installed, reachable, authenticated, and callable;
- timestamp and duration of a harmless smoke test;
- request/correlation ID and response status;
- token/usage metadata where available, without sensitive prompt content;
- timeout, rate-limit, quota, and fallback behavior;
- whether the call was made directly or through the ARTCB adapter;
- the evidence that proves the actual path.

### Proof-of-path protocol

1. Generate a unique synthetic correlation ID for a harmless test.
2. Have the adapter record the selected provider, declared model ID, adapter version, ARTCB API/MCP endpoint identity, and request ID.
3. Confirm the corresponding request in the ARTCB-side service telemetry or audit response, where available.
4. Verify the response schema and correlate it with the TERMINATOR-side event.
5. For direct provider calls, label them "direct provider"; do not label them ARTCB-mediated.
6. Repeat with the remote service unavailable and confirm the result becomes an explicit failure/degraded state rather than a false success.
7. Do not log API keys, authorization headers, raw secrets, or unnecessary sensitive prompt content.

**Acceptance criterion:** every model call has a verifiable execution-path label: `local-direct`, `provider-direct`, or `artcb-api` / `artcb-mcp`. A label alone is not sufficient; it must be supported by adapter and remote-side evidence where available.

## 7. KYC: distinguish a pipeline test from real-case certification

### Process

The documented ARTCB KYC pipeline has 12 stages and the R043 report describes an earlier offline, rule-based processing run covering five example forms and 120 of 124 fields, with four fields marked not applicable.

### Problem

An earlier successful example run is not equivalent to a current, end-to-end, production KYC validation. The reported test suite has one failure: the test expects `PROTECTED_WRITE`, while the implementation returns `PROTECTED_ZONE_OVERLAP`. The evidence also does not establish a current live API invocation from TERMINATOR, fresh external sanctions data, or full operational sign-off.

### Required validation

1. Resolve and document the expected semantics of the protected-zone validation code in the ARTCB repository through its own authorized maintenance process; do not patch that repository from this TERMINATOR audit.
2. Run the complete KYC suite in the supported Linux environment and preserve a sanitized test summary.
3. Use synthetic or appropriately authorized test documents; record input fixture versions and document hashes rather than exposing personal data.
4. Validate each stage's input/output schema, provenance, and failure behavior.
5. Test missing evidence, conflicting facts, non-applicable fields, sanctions matches, false positives, and unavailable sanctions sources.
6. Verify that sanctions alerts are explainable and that their data source/version and timestamp are recorded.
7. Exercise the KYC path through the intended API/MCP adapter from TERMINATOR, if that capability is in scope, and correlate each stage with the resulting evidence.
8. Explicitly distinguish offline fixture tests, remote integration tests, and authorized real-case operations.

**Acceptance criterion:** all required tests pass or have an explicitly approved, documented exception; every output is traceable to a fixture/source and rule/model version; no claim of production KYC certification is made until authorized end-to-end evidence exists.

## 8. Real-time forensic graph and progress semantics

### Process

The graph should render the actual event stream from intake through agent orchestration, tool/API calls, Guardian policy decisions, enforcement, containment, verification, and closure. Each event must have a stable run ID, event ID, sequence, timestamp, source/agent identity, event type, parent/correlation links, and evidence references where available.

### Problem

A visually active graph can mislead operators if its motion is simulated, if it displays only detection events, or if it labels an attack as blocked before the enforcement result is known. A percentage can also be misleading when its denominator is undefined.

### Required presentation

Maintain distinct progress values instead of one ambiguous percentage:

- **Attack-scenario progress:** completed scenario stages / planned scenario stages. This describes the simulation or observed attack path, not defensive success.
- **Detection status:** not evaluated, signals observed, detection candidate, or detection confirmed, with the evidence source.
- **Enforcement status:** pending, allow, block, escalate, or unknown; derive this from the authoritative policy/executor result.
- **Containment progress:** completed containment actions / required containment actions, with unknown and failed steps shown separately.
- **Remediation progress:** completed remediation steps / approved remediation plan steps.
- **Verification progress:** completed verification checks / applicable checks, with each check's result and scope.
- **Telemetry coverage:** expected instrumented sources reporting / expected instrumented sources, clearly labelled as coverage and never as "attack blocked percentage."

Do not calculate "99% blocked" from the number of displayed events. Do not show "100% resolved" until the required checks pass and the incident closure criteria are satisfied. Unknown, skipped, and unavailable checks must remain visible.

### Evidence rules

- Render actual received events, not timer-generated animations.
- Preserve event history when filtering or summarizing.
- Distinguish observed facts, detector verdicts, verified facts, hypotheses, and unknowns.
- Keep event time separate from ingestion time; show clock uncertainty when relevant.
- Mark missing telemetry as a gap, not as proof that no activity occurred.
- Record enforcement outcome independently of graph rendering, audio playback, or LLM summarization.
- Make every visible decision and progress metric drillable to its supporting event/evidence.

## 9. Voice UX: prerecorded cues plus concise summaries

### Process

A small reviewed library of prerecorded clips can announce meaningful phase changes without waiting for network TTS. Examples of cue classes include "Suspicious activity observed", "Policy block confirmed", "Containment started", "Verification incomplete", and "Incident closed". These are cue categories, not assertions to play before the corresponding evidence exists.

### Problem

A remote TTS call before each pipeline step can delay the security decision, consume quota, and produce too much speech during critical moments. A voice cue can also overstate the facts if the script is selected by stage name alone.

### Required design

1. Trigger prerecorded cues only from canonical, typed events and verified status transitions.
2. Distinguish "attack scenario started" from "intrusion detected" and "action blocked". Never announce a successful block until the authoritative executor/policy outcome confirms it.
3. Keep the corresponding text visible and accessible; voice must not be the sole channel for an alert.
4. Put audio on an independent, bounded queue. A stalled player, unavailable file, browser autoplay restriction, or failed TTS request must never block enforcement.
5. Prioritize critical detection, confirmed block, containment failure, and closure verification. Coalesce repetitive low-priority events.
6. During high-intensity phases, speak a short factual summary and the most relevant next action; preserve the full event stream for later forensic review.
7. At tactical pauses, provide a compact recap: what was observed, what was blocked or allowed, what remains unknown, and the next approved action.
8. Keep dynamic TTS optional and asynchronous. If it fails, show text and mark audio unavailable without delaying the pipeline.
9. Do not speak untrusted attacker-generated text verbatim as if it were a trusted system instruction.
10. Measure event-to-text latency, event-to-first-audio latency, queue delay, dropped/coalesced cues, and audio failure rate separately.

**Acceptance criterion:** with TTS disabled or delayed, policy decisions are emitted on the same enforcement path and within the same measured latency envelope as the text-only baseline. Browser testing confirms cue selection follows actual event states.

## 10. Security boundary for the ARTCB API/MCP adapter

- Start with the minimum set of read-only capabilities required for the first experiment.
- Treat MCP tool descriptions and remote outputs as untrusted data, not instructions that can override Guardian policy.
- Authenticate the service boundary, use TLS for remote traffic, validate schemas, and bind each operation to explicit authorization.
- Keep state-changing capabilities unavailable until separately reviewed and tested.
- Apply request-size, concurrency, timeout, retry, and budget limits.
- Use idempotency keys for retried operations that can mutate state.
- Preserve the existing Guardian enforcement path if ARTCB is unreachable; do not silently bypass or replace it.
- Use synthetic fixtures for integration tests and keep credentials out of source, prompts, audio, reports, and logs.
- Verify only the exact cryptographic ledger and event population covered by a check. A valid hash chain does not prove that no event was omitted.
- Do not give an agent blanket root/admin privileges as a substitute for a defined, auditable capability contract.

## 11. Implementation stages and exit gates

### Stage A — Baseline and branch reconciliation

- Record main and experiment branch SHAs.
- Review the full branch diff and preserve the R042/R043 reports.
- Reconcile the branch's divergence from current main without merging it into main.
- Confirm that no ARTCB implementation source or runtime logs are present in the TERMINATOR repository.

**Exit gate:** a reviewed, isolated branch based on an explicitly chosen baseline, with a clean, documented diff.

### Stage B — Contract and health proof

- Identify the authoritative ARTCB API/MCP endpoint and version.
- Obtain the API schema and MCP tool inventory from the running service, not only from documentation.
- Validate authentication, authorization, TLS, health semantics, timeout behavior, and error schema.
- Complete a synthetic read-only round trip with correlation IDs.

**Exit gate:** remote request/response and audit evidence agree; failures are explicit and safe.

### Stage C — LLM path verification

- Inventory local runtimes and configured API providers.
- Run one harmless smoke test per configured model/provider.
- Record the actual execution path and verify ARTCB mediation where claimed.
- Test quota exhaustion, timeouts, missing credentials, and provider unavailability.

**Exit gate:** every provider is classified as verified, failed, not configured, or not tested; no global "all LLMs operational" claim remains unsupported.

### Stage D — KYC evidence

- Resolve the known test mismatch through the ARTCB repository's own authorized workflow.
- Run the supported test suite and synthetic end-to-end adapter scenario.
- Verify provenance and evidence coverage at each stage.

**Exit gate:** all required tests pass or carry an approved exception; production readiness remains separately assessed.

### Stage E — Operator graph and voice

- Drive the graph from canonical events.
- Add separate attack, detection, enforcement, containment, remediation, and verification indicators.
- Add reviewed prerecorded cues and a bounded asynchronous audio queue.
- Test missing, late, duplicate, and out-of-order events; TTS delay/failure; and browser autoplay restrictions.

**Exit gate:** the graph and narration reflect actual evidence and never delay enforcement.

### Stage F — Final independent review

- Run unit, integration, browser E2E, failure-injection, and cross-host tests.
- Publish sanitized results, exact test scope, limitations, and outstanding risks.
- Compare the final branch diff with main.

**Exit gate:** a separate explicit owner decision is recorded before any merge. Passing the tests does not itself authorize the merge.

## 12. Required questions before calling the system production-ready

1. Which exact local and remote hostnames/endpoints are currently intended to participate, and which team controls each?
2. What health check proves that the remote ARTCB API is reachable and authenticated from the TERMINATOR runtime?
3. Which model IDs are actually installed locally, which providers are configured remotely, and which have passed a current smoke test?
4. Which LLM calls are direct provider calls, and which are demonstrably mediated by ARTCB API/MCP?
5. What is the authoritative API/MCP contract version and how are breaking changes detected?
6. Which KYC dataset is synthetic, which is authorized operational data, and which source/version supports sanctions screening?
7. What exact event population does each integrity/tamper check verify? Can an independent verifier reproduce the result?
8. What is the defined denominator for every progress percentage, and how are unknown or skipped stages represented?
9. Which event transitions trigger each prerecorded cue, and what evidence is required before saying "detected", "blocked", "contained", or "resolved"?
10. What are the measured enforcement latency and event-to-audio latency under provider timeout and network failure?
11. What is the recovery plan if the remote ARTCB API, MCP server, local model, or cloud provider is unavailable?
12. Who will approve the experiment's merge, and what explicit evidence must be reviewed first?

## 13. Final verdict

**Current status: limited Guardian scenario execution is documented; cross-host operation, complete LLM availability, live ARTCB-mediated execution, fully validated real-world KYC, and end-to-end voice/graph operation remain unproven.**

The correct next step is a staged, synthetic-data integration experiment on the isolated branch. The integration should remain optional and should never silently replace Guardian enforcement. ARTCB source must remain in its own repository and be consumed only through its documented, versioned interface.

**No application code was changed by this report. No external ARTCB repository was modified. No runtime logs or secrets were committed. No merge into `main` is authorized.**
