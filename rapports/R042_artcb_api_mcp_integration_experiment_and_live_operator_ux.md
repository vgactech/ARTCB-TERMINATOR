# R042 — ARTCB API/MCP Integration Experiment and Real-Time Defensive Operator UX

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Base:** `main` at the R041 report commit `059d11c3ef5a40f5fcfa80d79ed1972d93a98143`  
**Experiment branch:** `experiment/artcb-api-mcp-integration`  
**Status:** DESIGN / DECISION GATE — no application implementation performed by this report  
**Scope:** Architecture proposal for consuming a separately maintained ARTCB capability through documented API and MCP contracts, plus defensive live-operator narration and progress visualization. No source from another repository is copied or vendored. No runtime logs or secrets are included.

---

## 1. Executive decision

**Recommendation: proceed with a branch-isolated integration experiment, but do not merge it into `main` without explicit owner approval.**

The objective is to let ARTCB-TERMINATOR exercise externally provided ARTCB capabilities through stable API/MCP interfaces, while keeping the external implementation independently maintained and out of the TERMINATOR source tree. The integration must be optional, versioned, observable, and disableable. It must not silently replace existing Guardian behavior or become a mandatory runtime dependency until parity, failure handling, security, and competition-demo readiness are demonstrated.

This branch currently contains this report only. The repository-level project instruction limits this audit work to writing reports under `rapports/`; therefore this report does not implement application code, modify tests, change deployment settings, add secrets, or alter the external ARTCB repository. The branch is a decision and implementation specification, not proof that integration is already active.

**Merge policy:** no merge, rebase into `main`, or release promotion is authorized by this report. A separate, explicit approval is required after the acceptance gates in Section 13 pass.

## 2. Expertise activated

- API contract design and service integration.
- Model Context Protocol (MCP) tool integration and tool-boundary security.
- Rust/Python interoperability and versioned service boundaries.
- AI agent security, prompt-injection resistance, and tool-abuse containment.
- Identity, authentication, authorization, secret management, and auditability.
- Distributed tracing, provenance, event integrity, and replay.
- FastAPI/SSE streaming and browser-side event processing.
- Human-computer interaction for security operations.
- Voice UX, prerecorded audio cues, asynchronous text-to-speech, and accessibility.
- Reliability engineering, chaos testing, and staged rollout governance.
- Competition-demo architecture and evidence-based acceptance criteria.

## 3. Verified baseline and limits of this review

The GitHub connector confirmed that `vgactech/ARTCB-TERMINATOR` exists, uses `main` as its default branch, and is accessible to the connected account. R041 is present in the repository and documents the following issues in the current voice/SSE prototype:

1. Synchronous text-to-speech work can delay the security pipeline.
2. The frontend integration is not established by the reviewed R040 commit.
3. The event-chain narration needs to state precisely which recorded events were verified.
4. An enabled endpoint needs caller authorization and resource controls before untrusted exposure.
5. The current audio payload is a completed MP3 clip rather than progressive binary audio streaming.
6. Reconnect, replay, and durable event-delivery semantics are not yet demonstrated.

The previously reported test counts and local machine state are user-supplied claims, not independently reproduced by this report. The current machine's environment, Doppler authentication, AWS deployment, live provider credentials, browser playback, and complete test suite remain unverified here.

## 4. Integration principle: contract, not source-code import

### Process

TERMINATOR calls a separately deployed or locally hosted ARTCB-compatible service through a documented, versioned API and/or MCP server. TERMINATOR sends only the data required by the requested operation, receives structured results and evidence references, and records the interaction in its own event/provenance system.

### Problem

Copying or vendoring the external implementation into TERMINATOR would couple release schedules, complicate provenance, create accidental source duplication, and make it harder to test the external capability as an independent component. An undocumented or overly broad tool interface would also make behavior difficult to reproduce and audit.

### Solution

1. Define an adapter boundary in TERMINATOR, with a provider-neutral internal interface and a separately versioned external contract.
2. Prefer an HTTP API for stable request/response operations and use MCP for explicitly described agent tools where its tool-discovery and invocation semantics add value. Do not expose the same action through two uncoordinated paths.
3. Pin a supported API/MCP protocol version and record the provider version, capability set, request ID, and correlation ID with each run.
4. Keep external source code, private implementation files, and provider build artifacts out of this repository. Do not use a submodule or subtree to import that source.
5. Store only non-secret endpoint configuration and version metadata in ordinary configuration. Inject credentials at runtime through the existing approved secret-management path.
6. If the external service is unavailable or returns an incompatible schema, surface a clear degraded state and preserve the existing Guardian path; do not silently claim that the external capability ran.
7. Keep the integration behind a feature flag and default it off until the explicit acceptance gates pass.

**Required contract artifacts:** API/MCP capability inventory, request/response schemas, error taxonomy, authentication model, timeout/retry policy, version compatibility table, data classification, and test fixtures containing synthetic data only.

## 5. Trust boundary and security controls

### Process

The integration crosses a process and potentially a host boundary. Requests may contain prompts, event metadata, incident context, tool arguments, or evidence references. Responses may contain findings, proposed actions, confidence values, and structured evidence.

### Problem

A service response is not automatically trustworthy merely because it came from a named tool. It may be stale, malformed, incomplete, compromised, or influenced by untrusted input. MCP descriptions and tool outputs must be treated as data, not as instructions that override TERMINATOR policy. Credentials, unrestricted command execution, or arbitrary filesystem access would amplify the impact of a compromised agent or connector.

### Solution

- Authenticate service-to-service calls and validate the server identity. Use TLS; use mutual TLS or a short-lived scoped token where supported by the deployment.
- Authorize individual operations and validate every request/response against a versioned schema. Reject unknown fields when they alter security-sensitive semantics.
- Give each integration capability only the operations and resources needed for its defined task. Do not grant blanket root/admin authority to an agent merely to avoid implementation errors; enforce privileged actions through explicit policy checks and auditable execution.
- Apply bounded request sizes, timeouts, concurrency limits, rate limits, retry budgets, and circuit breakers. Never retry a non-idempotent action unless an idempotency key or equivalent deduplication contract is in place.
- Separate read-only analysis capabilities from state-changing capabilities. Require explicit policy authorization for actions with external side effects.
- Treat all remote tool output as untrusted. Sanitize rendered text, prevent output from becoming executable instructions, and bind any proposed action to a typed action schema.
- Keep credentials out of source files, committed environment files, prompts, audio narration, SSE payloads, telemetry labels, and logs. Check secret presence without printing secret values.
- Record the provider identity, version, capability invoked, decision scope, result status, latency, and evidence references. Never log raw secrets or unnecessarily duplicate sensitive payloads.
- Define an emergency feature-flag kill switch that disables the integration without disabling the existing defensive controls.

**Important assurance limit:** a signed response or valid hash proves integrity/authorship only within the scope of the verified key and payload. It does not prove that a remote analysis is complete, correct, or based on all relevant events.

## 6. Proposed execution flow

1. **Receive input:** accept the user's text or voice input and assign a stable run/correlation ID.
2. **Record intake:** persist the observable input metadata and applicable data-handling policy before downstream calls.
3. **Evaluate local policy:** classify the operation and determine which external capabilities are allowed.
4. **Call the adapter:** issue a bounded, authenticated API/MCP request with a schema version, idempotency key where applicable, and correlation metadata.
5. **Validate response:** validate schema, provider identity, status, evidence references, and the declared scope of any verification.
6. **Apply Guardian decision:** make allow/block/redact/escalate decisions in the authoritative policy path. Remote suggestions must not bypass that decision.
7. **Emit canonical event:** publish the structured event and decision immediately; do not wait for voice generation, animation, or optional summaries.
8. **Update the operator view:** update the live graph, timeline, status indicators, and progress metrics from actual received events.
9. **Narrate asynchronously:** play a short prerecorded phase cue when appropriate, then enqueue concise text/audio narration independently of enforcement.
10. **Persist and verify:** store provenance and evidence references, verify the declared integrity scope, and allow replay from persisted events.
11. **Close the incident:** record the final status, unresolved uncertainties, remediation outcome, and any recommended next actions.

A missing telemetry event must be shown as a telemetry gap, not interpreted as proof that no activity occurred.

## 7. Real-time voice and prerecorded phase cues

### Process

At the start of a predefined phase, the interface can play a short, locally available audio cue such as “Intrusion detected,” “Policy blocked the action,” “Containment in progress,” or “Incident verification complete.” These cues are selected from structured event types. Optional dynamic narration can summarize the latest verified state.

### Problem

Calling a remote text-to-speech provider before each pipeline step can delay enforcement, create unnecessary network dependencies, and cause repetitive or verbose narration during a critical response. A spoken claim can also overstate what the telemetry proves.

### Solution

1. Prepare a small, reviewed audio catalogue for high-value state transitions. Keep the clips short and make the corresponding text visible.
2. Trigger a clip only when a canonical event confirms that phase transition. Do not play “intrusion detected” merely because a scenario started; distinguish a simulated attack step from a confirmed detection.
3. Use a priority queue: critical detection/block/containment cues first, routine progress summaries second, and optional suggestions last. Deduplicate repeated cues by event ID and phase.
4. Never make Guardian enforcement wait for audio decoding, browser autoplay permission, network TTS, or audio-device availability.
5. If browser autoplay is blocked, show the text and an accessible play control. If audio fails, mark the audio status as unavailable while preserving the decision and event history.
6. Keep attacker-generated text explicitly labelled as untrusted scenario content. Do not let it directly choose authoritative voice prompts or policy claims.
7. Generate dynamic speech only from structured, evidence-gated templates. Use “not verified” or “unknown” whenever the evidence is incomplete.
8. Make voice volume, mute, playback rate, captions, and reduced-motion/quiet presentation user-configurable.

### Suggested cue catalogue

| Event type | Short cue | Trigger condition |
|---|---|---|
| Scenario started | “Security test started.” | Run has been accepted and assigned an ID |
| Suspicious behavior detected | “Suspicious activity detected.” | Detector emits a qualifying finding |
| Policy block confirmed | “Policy blocked the action.” | Authoritative executor/policy status confirms block |
| Containment started | “Containment in progress.” | A containment action has actually begun |
| Containment verified | “Containment verified.” | Required containment checks passed |
| Evidence integrity checked | “Evidence integrity check complete.” | State exact scope and result in the visual/text detail |
| Remediation completed | “Remediation checks complete.” | Required post-remediation tests passed |
| Incident closed | “Incident closed with unresolved items.” or “Incident closed; required checks passed.” | Select based on the actual final status, never a generic success template |

The audio clip is a concise notification, not the authoritative record. The structured event and evidence remain the source of truth.

## 8. Progress indicators must measure separate facts

### Process

The UI receives stage events, detector outcomes, policy decisions, and remediation results. It translates them into a timeline and measurable status indicators.

### Problem

A single percentage can be misleading if it mixes attack progression, detection confidence, blocking effectiveness, and remediation completion. For example, “95% protected” is not a defensible metric unless a defined denominator and measurement method exist. A progress animation must not invent work or advance solely because time has passed.

### Solution

Display separate indicators with explicit definitions:

- **Scenario progress:** completed predefined scenario stages divided by total planned stages. Label it “scenario progress,” not “security effectiveness.”
- **Detection status/confidence:** display the detector's actual score and calibrated meaning if available. Do not fabricate a percentage from a severity label.
- **Containment status:** show pending, running, confirmed, failed, or unknown for each required containment action. If a numerical percentage is needed, derive it from a fixed, disclosed checklist.
- **Remediation progress:** completed verified remediation checks divided by required checks; show failures and skipped checks separately.
- **Evidence coverage:** observed/expected event sources or checks, with missing telemetry visible. Do not equate coverage with proof of correctness.
- **Time metrics:** show elapsed time, time to first detection, time to policy decision, and time to verified containment separately when timestamps support those measurements.

Every metric must include its source, denominator or calculation rule, update time, and unknown/error state. Unknown must never be displayed as zero risk or 100% complete.

## 9. Short summaries and strategic suggestions without blocking execution

### Process

A background summarizer periodically reads a bounded window of canonical events and produces a compact status: what happened, what is confirmed, what remains unknown, what the defender has blocked, and what needs attention. A separate suggestion component may propose the next safe diagnostic or remediation step.

### Problem

Long summaries, extra LLM calls, or speculative recommendations can consume tokens and time, interrupt the operator, expose sensitive content, or delay the defensive process if they run synchronously. Suggestions can also be mistaken for completed actions.

### Solution

- Use a fixed compact format: **Observed / Confirmed / Blocked / Unresolved / Suggested next step**.
- Trigger summaries at meaningful phase transitions or at a configurable interval, not after every low-value event.
- Keep summarization in a separate bounded queue. It must never hold a lock needed by the policy engine or block event persistence.
- Use event IDs and watermarks so the summary can state exactly which events it covers. Mark late or missing events.
- Label every recommendation as a proposal, with rationale, evidence references, expected impact, and risk. Only an authorized executor may perform a state-changing action.
- Offer one or two high-value suggestions, ordered by urgency and reversibility, rather than flooding the operator with a long list.
- Add a “quiet/strategy mode” that suppresses routine speech and non-critical pop-ups while continuing to record events and raise critical alerts.
- Preserve full event history; compact summaries are indexes over the history, never replacements for it.
- If summarization times out, fails, or returns malformed content, keep the latest canonical status visible and mark the summary unavailable.

## 10. API/MCP adapter contract

The integration contract should define at least:

- Provider/service identity and protocol version.
- Capability name and description.
- Input schema and data classification.
- Output schema, status enum, evidence references, and declared verification scope.
- Authentication and authorization requirements.
- Correlation ID, request ID, and idempotency semantics.
- Timeout, cancellation, retry, rate-limit, and circuit-breaker behavior.
- Error categories: unavailable, unauthorized, forbidden, timeout, rate-limited, schema mismatch, integrity failure, and provider error.
- Data retention and redaction requirements.
- Health/readiness semantics that distinguish “configured” from “successfully reachable.”
- Compatibility policy and rollback behavior.
- Synthetic contract fixtures and conformance tests.

Do not interpret a successful HTTP response as a successful security operation. The response must contain a typed operation status and the evidence needed to substantiate any claim.

## 11. Failure modes and required behavior

| Failure | Required behavior |
|---|---|
| External API/MCP service unavailable | Mark dependency unavailable; preserve local defensive policy and the event trail |
| Authentication or authorization fails | Reject before invoking the protected capability; emit a sanitized security event |
| Timeout or cancellation | Stop waiting within the configured deadline; do not imply that the remote operation completed |
| Schema/version mismatch | Fail closed for that integration action; preserve diagnostic metadata without raw secrets |
| Duplicate request/retry | Deduplicate using the documented idempotency contract |
| Malformed or prompt-injected output | Treat as untrusted data; validate and do not execute embedded instructions |
| TTS provider timeout | Security decision and canonical event continue; show text and audio-unavailable status |
| Browser disconnect | Persist events independently; replay or clearly report the gap on reconnect |
| Audio autoplay denied | Display text and offer user-controlled playback |
| Missing telemetry | Mark source/coverage as unknown; do not infer absence of an attack |
| Summary unavailable | Keep structured status and event history intact |
| Feature flag disabled | Use the existing local Guardian path and clearly show that the external integration was not invoked |

## 12. Privacy, competition readiness, and dependency disclosure

The project should protect independently maintained implementation details by integrating through a stable external contract rather than copying private source files into TERMINATOR. Public documentation can describe the interface, version, capabilities used, and test evidence without publishing private source code or secret configuration.

At the same time, competition materials must accurately represent the architecture: if a separately maintained service is required for a demo, describe it as an external dependency and state which functions are performed by TERMINATOR versus that service. Do not claim that a capability is implemented natively in TERMINATOR if it is provided remotely. Do not include private repository URLs, source excerpts, access tokens, or non-public implementation details in public-facing materials unless their disclosure has been separately authorized.

This report records the engineering boundary and does not reproduce private source or secrets.

## 13. Branch governance and merge gates

**No merge is authorized.** The experimental branch is intentionally separate from `main). Before implementation is considered merge-ready, all of the following must be evidenced:

1. **Contract review:** API/MCP schemas, versions, authentication, data handling, and failure semantics approved.
2. **No-source-copy check:** confirm no external private source, build output, secret, or runtime log entered the TERMINATOR repository.
3. **Feature isolation:** external integration is optional and can be disabled without disabling existing Guardian enforcement.
4. **Security tests:** unauthorized calls do not invoke the provider; malformed responses, prompt injection, replay, duplicates, and rate limits are covered.
5. **Reliability tests:** provider outage, timeout, cancellation, and incompatible versions do not bypass local policy or destroy evidence.
6. **Voice isolation:** deliberately delayed or failed TTS does not delay the authoritative policy decision.
7. **UI proof:** a browser test confirms the graph updates from received events before completion; audio cues correspond to confirmed phase events.
8. **Metric validity:** progress values are derived from documented denominators and never simulated.
9. **Forensic validation:** correlation, event identity, provenance, chain scope, and replay behavior are tested.
10. **Operational readiness:** secret injection, endpoint configuration, TLS, health checks, and cost/resource limits are verified in the target environment.
11. **Competition demo rehearsal:** a deterministic scenario demonstrates attack, detection, policy decision, containment, evidence, and replay with clear degraded-state behavior.
12. **Explicit owner approval:** the repository owner explicitly approves the merge after reviewing the final diff and test evidence.

Passing a subset of these gates does not authorize merging. No automated merge, auto-merge, or release promotion should be enabled for this experiment.

## 14. Prioritized work plan

| Priority | Work item | Exit evidence |
|---|---|---|
| P0 | Recover and verify the new PC's repository path, Doppler session, venv, and toolchain | Sanitized environment checklist; no secret values exposed |
| P0 | Fix R041 enforcement/voice isolation and scope all evidence claims | Regression tests with delayed/failed TTS and scoped chain results |
| P0 | Specify the external API/MCP contract and security boundary | Reviewed schemas and provider/version compatibility table |
| P1 | Implement the adapter only after the report-only restriction is lifted or implementation is explicitly assigned | Adapter contract tests and no vendored source |
| P1 | Connect frontend graph/timeline to canonical live events | Browser integration tests, reconnect behavior, and event correlation |
| P1 | Add prerecorded phase cues and evidence-gated narration | Cue mapping tests, audio fallback, accessibility controls |
| P1 | Add valid progress metrics and concise background summaries | Metric unit tests, summary scope/watermark tests |
| P2 | Measure latency, provider cost, event throughput, and degraded-mode behavior | Reproducible benchmark report |
| P2 | Run the competition demo rehearsal and prepare transparent architecture notes | Recorded acceptance checklist and evidence bundle |

## 15. Final verdict

The proposed integration is feasible as a contract-based experiment and is preferable to copying external implementation code into TERMINATOR. The strongest design is to keep the external capability independently versioned, make every invocation explicit and auditable, retain Guardian as the authoritative policy enforcement path, and make voice, summaries, and visual animation strictly observational.

The live operator experience should combine short prerecorded cues at confirmed phase transitions, separately defined progress metrics, concise event-grounded summaries, and low-noise recommendations. None of these presentation features may block security decisions or substitute for persisted evidence.

**Current state: report and branch created; application integration not implemented or validated by this report. Main remains unchanged by this report. Merge requires explicit approval.**
