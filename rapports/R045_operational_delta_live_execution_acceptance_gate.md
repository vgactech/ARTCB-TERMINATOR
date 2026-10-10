# R045 — Operational Delta Audit, Live Execution Evidence, and Integration Acceptance Gate

**Date:** 2026-10-11  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch:** `experiment/artcb-api-mcp-integration`  
**Branch HEAD reviewed before this report:** `2d524b14ed1484b75d17b65a39dfffd6ed02a936`  
**Main HEAD reviewed:** `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844`  
**Previous experiment-branch report:** R044 — Forensic Readiness, ARTCB API/MCP Integration Gate, and Live Operator UX  
**Scope:** Reconcile the latest documented operational findings with the experiment branch, clarify what is and is not proven, and define evidence gates for live validation.  
**Change boundary:** This commit adds this report under `rapports/` only. It does not change application source, tests, deployment settings, secrets, runtime state, or any external repository.

---

## 1. Executive decision

**Current verdict: NOT CERTIFIED for full live end-to-end operation.** The repository documents working components and bounded scenario tests, but the available evidence does not establish that both environments are online and connected, that every local and API-backed LLM is callable, that all model calls are mediated by ARTCB API/MCP, that the KYC workflow is currently validated end to end, or that browser visualization and voice work through the full incident lifecycle.

The latest `main` report, R043, records important operational blockers: the OVH endpoint timed out; the inspected AWS competition role had no EC2 instances visible and lacked deployment permissions; the ARTCB API could not start in the reviewed Windows environment because of a POSIX-only `fcntl` import; the documented KYC test suite had one failure; the live `gpt-4o` attack failed because the configured OpenAI account had exhausted its credit balance; and the separate tamper-verification result reported a hash mismatch. These are evidence from the report history, not fresh tests performed by this report.

**Immediate priority:** establish fresh, timestamped runtime evidence for each environment and fix or explicitly disposition the integrity-verification defect before presenting the system as fully validated. Do not infer readiness from a green unit-test suite, a configured secret, an installed SDK, or an existing branch.

No merge, rebase, deployment, or application-code change is performed or authorized by this report.

## 2. Expertise activated

- Distributed systems and cross-host service verification.
- API/MCP contracts, adapter boundaries, and protocol compatibility.
- LLM runtime inventory and provider-path attestation.
- KYC pipeline validation, evidence provenance, and sanctions-data freshness.
- Cryptographic event integrity, tamper detection, and independent replay.
- Defensive AI orchestration, policy enforcement, and prompt-injection containment.
- Real-time observability, event correlation, and forensic reconstruction.
- SSE delivery, frontend integration, asynchronous audio, and accessible operator UX.
- Cloud IAM boundaries, secret-management hygiene, and deployment readiness.
- Test engineering, acceptance criteria, and change-control governance.

## 3. Repository synchronization and branch state

The GitHub state was checked before this report was written.

| Item | Observed value | Interpretation |
|---|---|---|
| Default branch | `main` | Authoritative current baseline for normal development |
| Main HEAD | `3ae0b9653be8fab8c6d51c4942407bfbbbd6e844` | Contains the latest R043 operational-readiness report |
| Experiment branch | `experiment/artcb-api-mcp-integration` | Existing isolated integration/design branch |
| Experiment HEAD before this report | `2d524b14ed1484b75d17b65a39dfffd6ed02a936` | Contains reports R042–R044 on the integration/UX gate |
| Merge base | `ef4c35cbacb177799efa21009b936db074630ea1` | Branches diverged after this commit |
| Comparison | Main and experiment are diverged; four commits on each side | A controlled reconciliation is required before implementation or a final diff review |

The comparison showed report files on the experiment side, including R042, R043, and R044. The branch name and design reports do **not** prove that an ARTCB API/MCP adapter has been implemented or that a remote service is connected.

**Branch-control rule:** keep the experiment isolated. Do not merge it into `main`, do not rebase it onto a new baseline, and do not promote it to a release without a separate explicit owner decision. Before implementation, create a reviewed branch reconciliation plan that preserves both the latest main reports and the experiment-branch reports. Do not resolve divergence by silently discarding reports or by force-updating a branch.

## 4. Current operational status: evidence versus claims

The following status table consolidates the most recent documented evidence. “Reported” means that a prior report recorded an observed result; it does not mean the test was rerun on 2026-10-11.

| Capability | Latest documented evidence | Current audit verdict |
|---|---|---|
| Guardian API startup and health | R042 reports local API health and scenario endpoints responding | Previously demonstrated locally; current process status not rechecked |
| Guardian policy scenarios | R043 reports ALLOW/BLOCK results for selected scenarios, with blocked tools not executed and evidence IDs present | Demonstrated only for the named scenarios |
| Recorded defender event chain | R043 reports R0 structural chain verification PASS for the tested scenarios | Narrowly demonstrated for that event population |
| Separate tamper-verification check | R043 reports FAIL with a genesis-hash/expected-hash mismatch | **Known integrity defect; not certified** |
| OpenAI-backed live attacker | R043 reports HTTP 500 caused by `credit_balance_exhausted` | **Blocked; live LLM interception not demonstrated** |
| All API LLM providers | No complete current provider-by-provider smoke-test inventory is documented | **Unknown / not certified** |
| All local LLMs | No current model inventory plus per-model call evidence is documented | **Unknown / not certified** |
| ARTCB API on Windows | R042/R043 report import failure due to `fcntl` | **Blocked on that environment** |
| OVH ARTCB endpoint | R043 reports timeout | **Not reachable in the last documented check** |
| AWS competition runtime | R043 reports no instances visible to the inspected read-only role and no deployment permissions | **Cross-host deployment not established by this evidence** |
| KYC pipeline | R043 reports an earlier offline five-form run and a 6/7 test result | Prior example run documented; full validation not certified |
| Frontend build | R042 reports successful TypeScript/build checks | Previously demonstrated build; browser E2E remains unproven |
| Voice endpoint | R042 reports configured ElevenLabs key status; R041 identifies end-to-end limitations | Configuration presence is not proof of browser audio playback |
| SSE reconnect/replay | Prior reports identify durable delivery and reconnect behavior as open | **Not certified** |
| ARTCB API/MCP adapter in the experiment branch | Branch comparison shows design/audit reports, not an implementation commit | **Not implemented by the reviewed branch state** |

A positive result for one layer must not be used to imply a positive result for another. For example, a valid chain for defender events does not prove completeness of every agent exchange; a successful frontend build does not prove browser-to-server connectivity; and an API key being present does not prove that the provider has quota or that a model call succeeds.

## 5. Process, problem, and solution: proving the two-environment path

### Process

A real cross-host operation requires a TERMINATOR process to send an authenticated request to a specific ARTCB API/MCP service, receive a structured response, and correlate both sides of the transaction. Each side must report enough non-secret metadata to identify the service, build, request, and result.

### Problem

Two source checkouts, two configured endpoints, or a local test suite do not establish that two running hosts communicate. The last documented OVH check timed out. The AWS inspection was limited by the permissions of the inspected role and therefore cannot establish the state of an organiser-managed environment outside that role's visibility.

### Required validation

1. Identify the actual runtime host and the authoritative ARTCB API/MCP endpoint for the test.
2. Record a non-secret service/build identifier, API/MCP protocol version, health status, authentication mode, and test timestamp on both sides.
3. From the actual TERMINATOR runtime, perform an authenticated health/readiness request.
4. Send one harmless, read-only synthetic request with a unique correlation ID.
5. Verify the request ID, correlation ID, provider identity, response schema, and result on both sides.
6. Measure request latency and distinguish connection failure, authentication failure, timeout, schema mismatch, provider error, and success.
7. Repeat with the remote service stopped or unreachable; TERMINATOR must show a clear degraded state and must not claim that ARTCB executed the request.
8. Confirm that Guardian's local enforcement path remains active when the external integration is unavailable.

**Acceptance gate:** a synthetic request is observed on both sides and correlated end to end, including the failure path. Until this passes, use the status “cross-host operation not certified.”

## 6. Process, problem, and solution: certifying LLM execution paths

### Process

Each LLM call should be attributable to one declared execution path: local model called directly, cloud provider called directly, or model/capability invoked through the ARTCB API/MCP boundary. These are distinct paths and must be reported separately.

### Problem

A configured environment variable, installed SDK, listed model name, or generic successful completion does not prove that the intended model is callable or that ARTCB mediated the operation. A call that bypasses the adapter must not be labelled ARTCB-backed.

### Required inventory

For each configured model/provider, record:

- provider name and execution mode;
- model identifier and revision/version, where available;
- runtime or service identifier, not a secret-bearing URL;
- installation status, reachability, authentication status, and smoke-test result;
- timestamp, duration, request/correlation ID, and response status;
- quota/rate-limit status and timeout behavior;
- whether the call was direct or ARTCB-mediated;
- evidence from the TERMINATOR adapter and, when available, the ARTCB-side service.

Do not record API keys, authorization headers, raw credentials, or unnecessary sensitive prompt content.

### Proof-of-path protocol

1. Generate a unique synthetic correlation ID for a harmless test prompt.
2. Record the selected provider, model ID, adapter version, route type, and request ID in a structured event.
3. For an ARTCB-mediated call, confirm the corresponding request in ARTCB-side telemetry or a signed/traceable response.
4. Validate the response schema and link it to the TERMINATOR-side event.
5. Repeat for each configured local runtime and API provider.
6. Exercise quota exhaustion, expired credentials, network timeout, invalid schema, and service unavailability.
7. Verify that a fallback, if configured, is explicitly recorded and does not falsely claim the original provider or ARTCB route succeeded.

**Acceptance gate:** every model path is classified as **verified**, **failed**, **not configured**, or **not tested**. “All LLMs are operational” is not an acceptable status unless each intended model has current evidence.

## 7. Process, problem, and solution: KYC readiness

### Process

The documented KYC pipeline has a multi-stage lifecycle and previously processed synthetic/example forms offline using rule-based resolution and context data.

### Problem

An earlier offline run is not equivalent to a current live KYC workflow. R043 records one failing test, `test_protected_zone_blocks_population`, where the expected validation code differs from the code returned by the implementation. The evidence does not certify current cross-host invocation, current sanctions-data freshness, or an authorized production case.

### Required validation

1. Keep any required fix to ARTCB's own repository and its authorized maintenance process; this TERMINATOR audit must not modify that repository.
2. Run the KYC suite in a supported environment and preserve a sanitized test summary.
3. Use synthetic or explicitly authorized data. Record fixture versions and hashes, not personal document contents.
4. Validate each stage's input/output schema, failure semantics, provenance, and evidence references.
5. Test missing evidence, conflicting facts, protected zones, non-applicable fields, sanctions matches, false positives, and unavailable sanctions sources.
6. Record the sanctions source/version and retrieval timestamp; stale or unavailable screening data must be explicit.
7. If KYC is called through API/MCP, correlate the TERMINATOR request with the ARTCB-side run and its stage outcomes.
8. Distinguish offline fixture testing, remote integration testing, and authorized real-case operation.

**Acceptance gate:** required tests pass or have a clearly documented and approved exception; every output is traceable to source/fixture and rule/model version; and no production certification is claimed without authorized end-to-end evidence.

## 8. Process, problem, and solution: integrity and tamper verification

### Process

The system serializes recorded events, compares event hashes with stored hashes, and checks parent links. A tamper test should deliberately alter a copy of an event or digest, detect the alteration, and prove that the original archive remains unchanged.

### Problem

R043 records a mismatch in which the observed value was the all-zero genesis hash rather than the expected stored event hash. That finding undermines confidence in the separate tamper-verification output. A PASS from a different structural replay check does not repair or supersede the failed tamper check.

### Required validation

1. Trace the lookup used by tamper verification from the event ID to the archived event and its stored digest.
2. Test an untampered event and require PASS.
3. Mutate a field in a test copy and require FAIL with the exact event ID and mismatching field.
4. Verify that the original archived event and digest remain unchanged.
5. Test an empty ledger, a single event, multiple chained events, a missing event, a duplicate event, and a broken parent link.
6. Run an independent verifier against the same exported synthetic fixture.
7. Ensure API and frontend labels distinguish structural chain verification from deliberate tamper detection and clearly show the scope of each check.

**Acceptance gate:** the clean fixture passes, the tampered fixture fails for the expected reason, and the original archive is unchanged. Until then, the UI must not present tamper verification as successful or fully operational.

## 9. Process, problem, and solution: live graph, progress, voice, and concise summaries

### Process

The operator interface consumes canonical events from intake through orchestration, API/MCP calls, policy decisions, containment, verification, and closure. It can show the graph and timeline, speak a short cue at meaningful phase transitions, and periodically summarize the latest confirmed status.

### Problem

A moving graph, an animated percentage, a configured voice API, or a generated sentence is not proof that a defensive action occurred. A single percentage can mix unrelated concepts such as attack progress, detection, containment, and remediation. Synchronous speech generation can also delay later pipeline stages.

### Required solution

**Event-driven graph**
- Render actual events, not timer-driven pseudo-events.
- Preserve history when filters or summaries change.
- Include stable event/run IDs, source/agent, event time, ingestion time, sequence, parent/correlation links, and evidence references where available.
- Mark missing telemetry as a coverage gap rather than proof that nothing happened.
- Distinguish observed, suspected, detected, confirmed, blocked, failed, and unknown states.

**Separate metrics**
- Scenario progress = completed planned stages / total planned stages.
- Detection = the actual detector state and score, only if its semantics are defined.
- Enforcement = authoritative ALLOW/BLOCK/ESCALATE/UNKNOWN result.
- Containment = completed verified actions / required containment actions.
- Remediation = completed verification steps / required remediation checks.
- Evidence coverage = reporting expected sources / expected sources.
- Latency = measured time from event to policy decision, containment, UI update, and first audio.

Every percentage needs a denominator and a source. Never use “99% protected” or “100% resolved” without a defined, evidence-backed calculation. Unknown, failed, and skipped checks must remain visible.

**Prerecorded voice cues**
- Trigger short reviewed clips only from canonical typed events and confirmed state transitions.
- Distinguish “scenario started,” “suspicious activity observed,” “policy block confirmed,” “containment verified,” and “incident closed.”
- Keep the matching text visible and accessible.
- Put audio on a bounded asynchronous queue; no policy decision may wait for playback, browser autoplay, network TTS, or audio hardware.
- Prioritize critical detection/block/containment-failure events, coalesce repetitive routine events, and support mute/quiet mode.
- If audio fails, preserve the event and show audio-unavailable status.

**Concise strategic summaries**
Use a fixed format: **Observed / Confirmed / Blocked or allowed / Unresolved / Suggested next action**. Summaries must identify the event IDs or time window they cover. Suggestions remain proposals and must not be described as executed actions. Summarization failure must not affect enforcement or erase the full event history.

**Acceptance gate:** browser E2E tests show that real events update the graph and that cues follow confirmed states. Delayed or disabled TTS must not change the security decision path or its measured latency envelope.

## 10. Integration boundary and safe rollout

The integration must use a documented, versioned API/MCP contract, not source-code copying. Keep the external implementation independently maintained and out of the TERMINATOR tree. Record provider identity/version, capability name, request ID, correlation ID, schema version, status, and evidence reference for each call.

Required controls:

- service authentication and TLS for remote calls;
- operation-level authorization and strict schema validation;
- bounded payload sizes, timeouts, concurrency, retry budgets, and rate limits;
- idempotency protection for retried state-changing requests;
- separation of read-only capabilities from state-changing capabilities;
- remote outputs treated as untrusted data, never as instructions that override Guardian;
- a feature flag that can disable the integration without disabling existing Guardian controls;
- explicit degraded-mode behavior when the provider is unavailable;
- no secrets in source, reports, UI payloads, narration, or committed logs.

Do not grant blanket root/admin privileges to an agent as a substitute for a defined capability contract. Privileged operations should be narrowly scoped, auditable, and enforced by policy.

## 11. Prioritized blockers and owners

| Priority | Blocker | Required action | Dependency |
|---|---|---|---|
| P0 | Tamper-verification mismatch recorded in R043 | Reproduce, correct through the authorized TERMINATOR code workflow, and validate clean/tampered fixtures | Code owner and test execution environment |
| P0 | Live OpenAI attack failed from exhausted quota | Restore provider quota or use an explicitly approved alternate test provider; rerun end-to-end | Account owner/provider |
| P0 | No fresh proof of cross-host API/MCP round trip | Identify actual endpoint and run correlated synthetic request from actual runtime | Host/operator access |
| P1 | ARTCB API import blocked by `fcntl` on Windows | Use supported Linux/WSL2 environment for validation; any source fix belongs to ARTCB's own workflow | Supported runtime |
| P1 | KYC test mismatch (6/7 PASS in R043) | Resolve expected validation semantics and rerun tests in ARTCB's authorized workflow | ARTCB maintainer |
| P1 | Local and API LLM inventory incomplete | Enumerate intended models and execute per-model smoke tests | Local host/provider access |
| P1 | Branches diverged | Prepare a no-loss reconciliation plan and review diff before any implementation | Repository owner |
| P1 | Browser E2E for SSE/voice not certified | Test actual browser-to-API event delivery, playback, disconnect/reconnect, and replay | Browser and running services |
| P2 | Progress percentages could be semantically ambiguous | Define denominator/source for each metric and test unknown/failure states | UI/observability owner |
| P2 | Voice narration may be delayed or excessive | Use prerecorded critical cues and bounded asynchronous narration queue | UI/audio implementation |

No external blocker should be silently converted into a PASS. Where credentials, provider quota, endpoint ownership, or runtime access are unavailable, record the item as blocked and name the dependency.

## 12. Required questions before certification

1. What are the exact hostnames and service identities of the two intended runtime environments?
2. Can the actual TERMINATOR runtime authenticate to the actual ARTCB API/MCP endpoint right now?
3. What protocol version and capability inventory does the running ARTCB service report?
4. Which local model IDs are installed, and which have passed current inference smoke tests?
5. Which API providers are configured, funded, authenticated, and currently callable?
6. For every model call, what evidence proves whether the route was local-direct, provider-direct, ARTCB API, or ARTCB MCP?
7. Can an independent verifier reproduce the tamper-verification result on clean and deliberately altered fixtures?
8. Has the KYC test mismatch been resolved through the ARTCB repository's own authorized workflow?
9. Which sanctions sources and versions are used, and how are freshness and unavailability represented?
10. Has a real browser session verified the SSE stream, event graph, voice playback, and reconnect/replay behavior?
11. What is the denominator and evidence source for every displayed progress percentage?
12. What are the measured enforcement latency and event-to-audio latency when the LLM/TTS provider is slow or unavailable?
13. What is the approved rollback behavior if API/MCP compatibility breaks during the experiment?
14. Who will explicitly approve any eventual merge after reviewing test evidence and the complete branch diff?

## 13. Final verdict and next sequence

**Status: NOT CERTIFIED for full live operation.** The reports document selected local behavior and tests, but important live dependencies and end-to-end proofs remain absent or blocked.

Recommended order:

1. Reproduce and resolve the tamper-verification defect; do not treat the separate chain PASS as a substitute.
2. Restore a working LLM provider path and prove one live generated attack is intercepted, with a correlated event trail.
3. Run a synthetic authenticated ARTCB API/MCP round trip from the actual TERMINATOR runtime.
4. Complete per-model inventory and classify every intended provider as verified, failed, not configured, or not tested.
5. Resolve the documented KYC test mismatch through ARTCB's own authorized workflow and rerun the supported suite.
6. Validate browser event visualization, voice cues, compact summaries, and failure/reconnect handling.
7. Reconcile the diverged branches without losing reports, review the full diff, and run the acceptance suite.
8. Obtain separate explicit approval before any merge or release promotion.

**Change record:** this report only was added under `rapports/`. No application code, test, configuration, secret, deployment, or external ARTCB repository was modified. No runtime logs were committed. No merge, rebase, or deployment was performed.
