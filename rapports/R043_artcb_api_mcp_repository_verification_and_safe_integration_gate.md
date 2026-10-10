# R043 — ARTCB API/MCP Repository Verification and Safe Integration Gate

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Target branch:** `experiment/artcb-api-mcp-integration`  
**Predecessor:** R042 — ARTCB API/MCP Integration Experiment and Real-Time Defensive Operator UX  
**Status:** READ-ONLY REPOSITORY REVIEW / DESIGN GATE — no application implementation performed  
**Scope:** Verify repository accessibility and the currently documented ARTCB API/MCP surface; define a branch-isolated, no-vendoring integration plan and operator UX requirements. This report contains no secrets, runtime logs, private source excerpts, or copied implementation files from the external repository.

---

## 1. Executive decision

**Proceed with a staged API/MCP integration experiment on the existing experimental branch. Do not merge it into `main` without explicit owner approval.**

The repository review confirms that ARTCB documents an API and contains an MCP server implementation on its `main` branch. The separately named `artcb_API` and `artcb_MPC` repositories are currently empty according to GitHub's contents API; therefore they must not be treated as the source of truth for the working API/MCP implementation. The currently documented implementation lives in the independently maintained `artcb` repository.

TERMINATOR should consume ARTCB only through a stable, versioned API and/or MCP contract. It must not copy, vendor, submodule, subtree, or otherwise import ARTCB implementation source into this repository. This experiment must remain isolated from the current product baseline. No merge, release promotion, or automatic merge is authorized.

This is a report-only change. No TERMINATOR application code, test code, deployment configuration, credentials, or external repository content is changed by this report.

## 2. Expertise activated

- Repository and branch provenance review.
- API contract design and Python service interoperability.
- Model Context Protocol (MCP) tool discovery and invocation.
- Application security, authorization, and trust-boundary analysis.
- AI-agent tool safety and prompt-injection containment.
- Event provenance, audit trails, and replay semantics.
- Reliability engineering, timeouts, idempotency, and degraded modes.
- Real-time operator UX, accessibility, and alert prioritization.
- Prerecorded audio cues, asynchronous narration, and voice failure handling.
- Metrics design and evidence-based progress visualization.
- Branch governance, test gates, and competition-demo integrity.

## 3. Repository access and evidence

### 3.1 ARTCB main repository

GitHub access confirmed `vgactech/artcb` exists, is private, and has `main` as its default branch. The connected GitHub account was able to read its README, API reference, MCP server module, MCP tool definitions, MCP setup guide, and MCP tests.

The README describes a Python/FastAPI service, REST and WebSocket interfaces, memory/graph functions, agent workflows, and a separate MCP server. These are repository-documented capabilities, not independently reproduced runtime results.

Relevant repository documents inspected:
- `README.md`
- `API_REFERENCE_ARTCB.md`
- `src/artcb/mcp/server.py`
- `src/artcb/mcp/tools.py`
- `src/artcb/sdk/artcb_sdk.py`
- `docs/MCP_SETUP.md`
- `tests/test_mcp_server.py`
- `rapports/086_mcp_interop_multienv_2026_07_31.md`

### 3.2 Separately named API and MCP repositories

GitHub's repository metadata reports both `vgactech/artcb_API` and `vgactech/artcb_MPC` as existing repositories with `main` as the default branch, but attempts to read `README.md` returned GitHub's explicit “repository is empty” response. No branches were returned by the branch search for either repository.

**Interpretation:** these repositories cannot currently be used as implementation references. Their existence does not establish that they contain a deployable service. Recheck their contents before any future integration milestone.

### 3.3 TERMINATOR experimental branch

The report R042 exists on `experiment/artcb-api-mcp-integration`. It defines the architectural direction and operator UX, but it explicitly states that application integration has not been implemented by that report. This R043 adds repository-grounded findings and acceptance gates; it does not claim the adapter or UI already exists.

### 3.4 Verification limits

This review reads repository contents through GitHub. It does not prove:
- that a local ARTCB process is running or reachable;
- that a live endpoint is healthy or authenticated;
- that the checked-in API/MCP code passes tests in the current environment;
- that every documented tool behaves as described at runtime;
- that remote credentials, Doppler projects, or deployment resources are correctly configured;
- that the current local checkout matches the inspected remote commit.

Those items require a controlled runtime verification phase with synthetic data and sanitized results.

## 4. What the documented ARTCB API/MCP surface provides

The API reference documents endpoints for health and metrics, encoding/decoding, graph retrieval, search/store, agent execution, chain verification, Proof-of-Learning status, wallets, mining, pools, P2P, groups, connectors, notifications, and dashboard data. Exact route availability and authorization must be verified against the target runtime and its OpenAPI document before the adapter depends on any route.

The MCP server source documents:
- a stdio transport for local agent/IDE integrations;
- an HTTP transport selectable by host and port;
- MCP operations for initialization, tool listing/calls, resources, prompts, and ping;
- a configurable API base URL, defaulting to a local API endpoint;
- tool definitions that include read-oriented queries and state-changing operations.

The tool definitions include examples of read-only or low-impact operations (identity/status, search, chain verification, wallet balance) and state-changing operations (memo/event writes, thinking that may write a result, mining, and external transaction import). The adapter must not expose all tools to the defensive workflow merely because they are discoverable.

## 5. Initial security findings from static code inspection

These are code-review observations, not claims of a successful exploit or proof that the service is deployed with unsafe settings.

### Finding S1 — HTTP transport has no authentication visible in the inspected handler

**Process:** the MCP HTTP handler accepts POST requests, parses JSON-RPC, and dispatches them to the server. Its health route returns a fixed healthy response.

**Problem:** the inspected handler does not visibly authenticate the caller or authorize individual tools. Its default host is `0.0.0.0`, which binds to all interfaces unless deployment arguments override it. If used on an untrusted network, write-capable tools could become reachable without the intended trust boundary. The fixed health response does not establish that the downstream ARTCB API is reachable.

**Required action before network exposure:**
1. Prefer stdio for same-machine experiments where practical.
2. For HTTP, bind to loopback by default for local testing. Remote deployments must use an authenticated, encrypted service boundary and network controls.
3. Add caller authentication and per-tool authorization before enabling write operations.
4. Make readiness probe the downstream dependency with a bounded timeout, while keeping liveness distinct from readiness.
5. Test unauthorized, malformed, oversized, and rate-limited requests.
6. Do not expose the HTTP listener directly to the public Internet during the experiment.

### Finding S2 — MCP tool errors may be returned as ordinary text

**Process:** tool execution catches exceptions and can return a text message. The server's inspected tool-call handler wraps the returned content with `isError: false`.

**Problem:** a caller can misinterpret an error message as a successful tool result if the adapter trusts only the top-level response status.

**Required action:** normalize tool results into an adapter-owned typed status: `succeeded`, `failed`, `unavailable`, `unauthorized`, `timed_out`, or `unknown`. A human-readable message alone must never establish success. Confirm success from structured response fields and, where appropriate, a subsequent read-only verification.

### Finding S3 — Error details can propagate across the boundary

**Process:** inspected code builds errors from exception text and may include a truncated downstream HTTP response body.

**Problem:** exception text can contain internal implementation details or sensitive provider responses. Even if tokens are not intentionally printed, raw error propagation increases disclosure risk.

**Required action:** return sanitized error categories and a correlation ID to TERMINATOR. Keep detailed diagnostics only in the protected service's own redacted telemetry. Never include tokens, passwords, environment dumps, raw secrets, or full sensitive response bodies in TERMINATOR UI, audio, or logs.

### Finding S4 — MCP discovery includes side-effecting capabilities

**Process:** the server exposes a tool catalogue that includes operations for memory writes, mining, and importing an external transaction, in addition to reads and verification.

**Problem:** allowing an autonomous defensive agent to invoke every discovered tool would grant capabilities unrelated to incident analysis and could cause persistent state changes.

**Required action:** maintain a TERMINATOR-side explicit allowlist. Begin with read-only capabilities only. Add writes later only when the use case is justified, the request schema is constrained, the identity/visibility semantics are understood, and a separate policy gate authorizes the action. Never map an incident recommendation directly to a persistent write or external transaction import.

### Finding S5 — API and MCP contract compatibility is not yet proven

**Process:** the API reference, SDK, MCP server, and tool implementations are separate layers. The MCP server delegates to the API using endpoint paths and payloads.

**Problem:** a documented endpoint or schema can drift between versions. The presence of an SDK or MCP tool does not prove that the corresponding endpoint exists and is compatible in a particular deployment.

**Required action:** pin the tested provider revision and supported API/MCP versions; capture the OpenAPI schema hash or a reviewed contract version; run schema and smoke tests against the target service; reject unknown incompatible versions rather than guessing.

### Finding S6 — API reachability and MCP reachability are distinct states

**Process:** TERMINATOR may be able to connect to the MCP listener while the underlying API is unavailable, or may reach the API while the MCP process is not running.

**Problem:** a single “connected” indicator can incorrectly imply the entire dependency chain is healthy.

**Required action:** show separate states for configuration, MCP transport, downstream API, authentication, and capability readiness. A successful health response from the MCP HTTP handler alone is not proof of end-to-end readiness.

## 6. Recommended integration topology

1. TERMINATOR's existing Guardian policy path remains authoritative.
2. A provider adapter translates a small internal capability interface into version-pinned ARTCB API/MCP requests.
3. The adapter sends only the minimum necessary data, with a request ID, correlation ID, timeout, and idempotency key for any permitted write.
4. The adapter validates response schema, operation status, provider version, and evidence scope.
5. Guardian independently decides whether to allow, block, redact, or escalate.
6. Canonical incident events are persisted before optional UI narration or summarization.
7. The UI consumes the canonical event stream, not unverified claims from tool text.
8. The feature flag can disable the external integration without disabling existing Guardian controls.

**Initial capability profile:** health/readiness, identity/capability metadata where safe, semantic search on synthetic or explicitly approved data, and chain verification limited to a declared scope. Keep memo/write, mining, bridge import, wallet creation, token movement, and other persistent or external side effects disabled in the first phase.

## 7. Voice UX: phase cues without enforcement latency

### Process

A predefined phase transition emits a canonical event. The UI maps that event to a short prerecorded cue and visible text. Dynamic narration, if enabled, is generated from a bounded summary of verified events and runs in a separate queue.

### Problem

Remote TTS, audio decoding, browser autoplay restrictions, or long summaries must not delay detection, policy decisions, containment, or evidence persistence. Spoken statements can also overstate what telemetry proves.

### Required solution

- Use a small, reviewed audio catalogue for high-value events.
- Trigger a cue only after the corresponding event is confirmed; a scenario starting is not the same as an intrusion being detected.
- Prioritize confirmed detection, policy block, containment start/failure, verified containment, and incident closure.
- Deduplicate by canonical event ID and phase.
- Never await audio playback or remote TTS on the enforcement path.
- Always display equivalent text; if audio is unavailable or autoplay is denied, continue silently and show the reason.
- Label simulated scenario events as simulated. Do not narrate them as real-world intrusions.
- Keep untrusted attacker-controlled text out of authoritative alert templates.
- Provide mute/quiet mode, captions, volume controls, and user-triggered replay.
- Use “unknown” or “not verified” when evidence is incomplete.

Suggested cue catalogue:

| Canonical event | Short cue | Evidence required |
|---|---|---|
| `scenario.started` | “Security test started.” | Run accepted and run ID assigned |
| `finding.confirmed` | “Suspicious activity detected.” | Detector emitted a qualifying finding |
| `policy.block.confirmed` | “Policy blocked the action.” | Authoritative policy/executor confirms the block |
| `containment.started` | “Containment in progress.” | Containment operation actually started |
| `containment.verified` | “Containment verified.” | Required containment checks passed |
| `evidence.check.completed` | “Evidence check complete.” | The displayed detail names the exact verification scope |
| `remediation.checks.completed` | “Remediation checks complete.” | Required post-remediation checks have results |
| `incident.closed` | Select a status-specific message | Final status and unresolved items are known |

The spoken cue is a notification, not the authoritative record. The canonical event and evidence references remain the source of truth.

## 8. Progress display: separate metrics, no fabricated percentage

A single “protection percentage” would mix unrelated quantities and is not acceptable without a defensible definition. Show separate, evidence-derived fields:

- **Scenario progress:** completed planned scenario stages / total planned stages.
- **Detection:** actual detector result, score, severity, and calibration meaning if available. Do not convert severity labels into invented percentages.
- **Policy outcome:** pending, allowed, blocked, escalated, failed, or unknown.
- **Containment:** pending, running, verified, failed, or unknown for each required action.
- **Remediation:** passed required checks / total required checks, with skipped and failed checks shown separately.
- **Evidence coverage:** observed expected sources/checks / total expected sources/checks, with missing telemetry called out.
- **Latency:** time to first detection, policy decision, and verified containment only where timestamps support the calculation.

Each metric must disclose its denominator/calculation rule, source event IDs, last update, and unknown/error state. Unknown must not be displayed as zero risk or complete. Progress must advance only from real events or completed checks, never from an animation timer.

## 9. Short summaries and strategic suggestions

Use a fixed compact structure: **Observed / Confirmed / Blocked / Unresolved / Suggested next step**.

- Summaries run in a separate bounded queue and never hold a lock needed by policy enforcement or event persistence.
- Each summary includes a watermark or event-ID range so the operator knows which evidence it covers.
- Late or missing events are marked explicitly.
- Suggestions are proposals, not completed actions. Show rationale, evidence references, expected impact, reversibility, and risk.
- Offer one or two high-value suggestions rather than flooding the operator.
- A quiet/strategy mode suppresses routine speech and low-priority popups but preserves event recording and critical alerts.
- A summary timeout or malformed result does not erase the last canonical status.
- Preserve the full event history; summaries are indexes, never replacements.

## 10. Data minimization and memory writes

ARTCB's documented MCP tools can persist content. Incident data may include secrets, personal data, credentials, or attacker-controlled instructions. It must not be written to a persistent ARTCB store by default.

Before any approved write is enabled:
1. Define exactly which fields may be stored and why.
2. Redact secrets and unnecessary personal data before the boundary.
3. Use synthetic fixtures for integration tests.
4. Require an explicit policy decision for each write class.
5. Enforce the intended visibility and identity at the API layer, not only in UI controls.
6. Use idempotency keys and verify the resulting operation status.
7. Make retention, deletion, and access scope explicit.
8. Prohibit credentials, session tokens, full environment dumps, and raw runtime logs from being stored in prompts, audio, events, or memory.

## 11. Branch and repository separation rules

- Keep this experiment on `experiment/artcb-api-mcp-integration`.
- Add report artifacts only under `rapports/` while the report-only restriction remains in force.
- Do not copy, vendor, submodule, subtree, or commit source files from `vgactech/artcb`, `vgactech/artcb_API`, or `vgactech/artcb_MPC` into TERMINATOR.
- Do not commit runtime logs, credentials, tokens, private environment files, generated database state, or unreviewed test data.
- Do not change ARTCB or its API/MCP repositories as part of this TERMINATOR task.
- Do not merge this branch, rebase it into `main`, enable auto-merge, or promote a release without explicit owner approval.
- Any later implementation must be reviewed as a separate change set and must not be represented as complete until tests and runtime evidence exist.

Public-facing architecture descriptions should accurately identify the external service boundary and distinguish capabilities performed by TERMINATOR from those provided by an external service. They should not reproduce private source, credentials, or internal implementation details that are not intended for publication.

## 12. Acceptance gates before any merge request is considered ready

1. **Repository boundary:** diff proves only authorized report files changed during the report-only stage; no external source or runtime logs are included.
2. **Provider contract:** supported API/MCP versions, tool schemas, auth model, error categories, data classification, and idempotency are documented.
3. **Read-only pilot:** synthetic-data tests pass for readiness, search, and declared-scope verification.
4. **Authorization:** unauthenticated and unauthorized calls are rejected before protected capabilities execute.
5. **Side-effect denial:** all write-capable tools are denied by default in the first integration profile.
6. **Error semantics:** timeouts, provider errors, schema mismatch, malformed output, and false-success tool responses become typed failure states.
7. **Prompt-injection resistance:** remote tool output is treated as data and cannot override Guardian policy or trigger arbitrary tools.
8. **Reliability:** provider outage, cancellation, retry, duplicate request, and circuit-breaker behavior are tested.
9. **Evidence:** every decision and metric can be traced to canonical event IDs and a stated verification scope.
10. **Voice isolation:** delayed/failed audio and TTS cannot delay enforcement or event persistence.
11. **UI proof:** browser tests show event-driven progress, unknown states, audio fallback, reconnect behavior, and quiet mode.
12. **Performance:** latency, concurrency, resource limits, and provider costs are measured under a repeatable synthetic scenario.
13. **Demo rehearsal:** a deterministic scenario demonstrates event intake, detection, policy decision, containment status, evidence, and replay, including a dependency outage.
14. **Explicit approval:** the repository owner reviews the final diff and test evidence and separately approves any merge.

Passing these gates does not itself authorize a merge; explicit approval remains mandatory.

## 13. Prioritized plan

| Priority | Work item | Exit evidence |
|---|---|---|
| P0 | Confirm the local API/MCP processes and their exact version in a controlled environment | Sanitized readiness results; no secret values |
| P0 | Review and secure the MCP HTTP trust boundary before any network exposure | Authentication/authorization tests and safe bind configuration |
| P0 | Define a minimal read-only adapter contract | Versioned schema, tool allowlist, and error mapping |
| P1 | Implement the adapter only after report-only restrictions are lifted by explicit instruction | Contract tests and source-separation scan |
| P1 | Connect canonical events to the live operator UI | Browser integration tests and replay evidence |
| P1 | Add prerecorded cues and asynchronous concise summaries | Event-to-cue tests, audio fallback, summary watermarks |
| P1 | Add evidence-based progress metrics | Metric calculation tests with unknown/error cases |
| P2 | Run fault-injection and performance tests | Reproducible benchmark and outage report |
| P2 | Rehearse the competition demonstration | Deterministic evidence bundle and approved architecture summary |

## 14. Final verdict

The repository evidence supports the feasibility of integrating ARTCB through its documented API and MCP service without importing ARTCB source into TERMINATOR. The separate `artcb_API` and `artcb_MPC` repositories are empty at the time of this review; the working contract references inspected here are in the main ARTCB repository.

The primary blocker is not the absence of an API/MCP design. It is the need to establish a safe, versioned, authenticated and testable boundary, especially because the documented MCP tool catalogue includes persistent side effects and the inspected HTTP handler does not visibly enforce caller authentication. Begin with a read-only, synthetic-data pilot and keep Guardian authoritative.

The voice/progress concept is viable if prerecorded cues and summaries remain observational and asynchronous, while all percentages derive from real, documented measurements.

**Current state: R042 and this R043 report only; no application adapter or UI integration has been implemented or runtime-validated by these reports. The experimental branch remains unmerged. Any merge requires explicit owner approval.**
