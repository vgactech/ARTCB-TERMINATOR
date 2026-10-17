# R071 — Critical Audit of R070 Guardian MCP, ElevenLabs, Doppler, and OVH2 Deployment Claims

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Scope:** Documentation-only audit of the R070 deployment summary supplied for review, reconciled against the latest repository state available through the connected GitHub account.  
**Change policy:** This commit adds this report only. No application code, tests, deployment configuration, secrets, logs, external ARTCB repository, or infrastructure were modified.

## 1. Executive conclusion

**Overall status: NOT INDEPENDENTLY CERTIFIED.**

The supplied R070 summary reports that, on OVH2, `artcb.service` is disabled/stopped, `artcb-guardian.service` is active on port 8002, `guardian_mcp` is deployed, an ElevenLabs credential is injected through Doppler, voice is enabled with four active voices, the HTTPS frontend presents the TERMINATOR 3D interface, and HTTP redirects to HTTPS.

These are operational claims, not independently established facts in this audit. No live SSH session, systemd query, HTTP request, Doppler metadata query, authenticated MCP call, ElevenLabs synthesis request, browser session, or deployment health check was available to execute here. Accordingly, each claim is classified as **reported / requires live evidence**, not PASS.

The latest repository commit visible to this audit is `4c43eac38bdad90d510fd93de06338fcf284b098` (2026-10-17 03:17:33 UTC), titled `docs: add R066 — fix port 8002 + start_guardian.sh + demo live APPROVED`. Its report documents a local/macOS launch path and a reported KYC/SSE demonstration. It explicitly states `DEBUG` mode, `CERTIFIED_100=false`, and `unique_human_proven=false`. Those caveats must not be silently upgraded to a production certification.

The R070 path provided in the conversation was not retrievable from the repository's default branch during this audit. Therefore this report audits the **R070 status summary supplied in the conversation**, not the unavailable R070 file itself. This is a repository-visibility limitation, not proof that the file does not exist on another branch or machine.

## 2. Expertise activated

- Linux service management and systemd operations.
- Deployment verification and environment parity.
- Python/FastAPI service health and port isolation.
- MCP protocol integration and authentication boundaries.
- Secret management and credential lifecycle (Doppler).
- ElevenLabs text-to-speech integration and failure isolation.
- HTTPS/TLS and HTTP-to-HTTPS redirect validation.
- Frontend/backend integration and end-to-end observability.
- Security evidence, provenance, auditability, and release acceptance criteria.
- Git repository integrity and documentation-only change control.

## 3. Evidence boundary and repository synchronization

### 3.1 Repository evidence observed

The connected GitHub view returned the following recent commit as the latest visible repository commit:

- Commit: `4c43eac38bdad90d510fd93de06338fcf284b098`
- URL: https://github.com/vgactech/ARTCB-TERMINATOR/commit/4c43eac38bdad90d510fd93de06338fcf284b098
- Message: `docs: add R066 — fix port 8002 + start_guardian.sh + demo live APPROVED`

The commit's report describes:
- Guardian expected on port 8002, while port 8001 was occupied by another ARTCB service on the reported development machine.
- A `start_guardian.sh` launch helper using `python3 -m uvicorn`.
- A reported KYC stream containing `guardian_decision: BLOCK`, `chain_verified: R0 PASS`, and a final KYC verdict of `APPROVED`.
- Explicit development/debug caveats: `CERTIFIED_100=false` and `unique_human_proven=false`.

This is repository documentation evidence. It does not independently prove that the OVH2 production environment is currently in the same state.

### 3.2 Evidence not available

The following were not independently accessible during this audit:
- The R070 report at the supplied path.
- A live OVH2 shell or systemd state.
- Current service logs or journal entries.
- Current process/socket ownership for TCP port 8002.
- A live HTTPS/TLS handshake and redirect response.
- Doppler project/config metadata or a runtime confirmation of secret injection.
- An authenticated request through the deployed Guardian MCP endpoint.
- A successful ElevenLabs synthesis call and playback test in the actual frontend.
- A browser-level end-to-end session proving that backend events drive the visible 3D frontend.

**Interpretation:** the deployment summary is useful as a checklist of assertions to validate, but is not itself sufficient evidence for certification.

## 4. Claim-by-claim assessment

| Component / claim | Reported state | Audit status | Required proof |
|---|---|---|---|
| `artcb.service` | Disabled and stopped | NOT VERIFIED | `systemctl is-enabled artcb.service`, `systemctl is-active artcb.service`, and unit/process inventory |
| `artcb-guardian.service` | Active on port 8002 | NOT VERIFIED | `systemctl is-active artcb-guardian.service`, `systemctl status`, `ss -ltnp`, and health endpoint response |
| `guardian_mcp` | Deployed | NOT VERIFIED | Service/package identity, version or commit, authenticated MCP initialize/list-tools/request round trip, and correlated server-side event |
| Doppler credential injection | Credential injected | NOT VERIFIED | Confirm the expected variable name is present in the running service environment without printing its value; verify Doppler project/config and access policy metadata |
| ElevenLabs | `voice_enabled: true`; four voices active | NOT VERIFIED | Sanitized runtime configuration, successful synthesis request, returned audio metadata, and frontend playback confirmation |
| Frontend | HTTPS URL shows TERMINATOR 3D UI | NOT VERIFIED | HTTP status, TLS certificate/hostname validation, browser console/network checks, and a live event-to-render test |
| HTTP to HTTPS | 301 redirect | NOT VERIFIED | Request to the HTTP origin showing status 301 and a correct HTTPS `Location` header; verify no redirect loop |
| KYC / Guardian integration | Previous report describes APPROVED and BLOCK events | HISTORICAL REPORT ONLY | Re-run a deterministic authorized test and correlate emitted SSE events, decision record, and chain verification |
| Forensic certification | No current certification claim proven | NOT CERTIFIED | Define and pass release acceptance criteria; preserve the explicit `CERTIFIED_100=false` caveat until evidence supports a change |

## 5. Process, problem, and solution

### 5.1 Service ownership and port isolation

**Process.** systemd supervises a service unit; the process binds a network socket; the frontend targets a configured API base URL.

**Problem.** A service can appear configured while the process is stopped, crash-looping, listening on a different interface, or sharing a port with an unrelated process. The earlier R066 report describes port 8001 conflict on a development machine and a move to port 8002. That history does not establish current OVH2 socket ownership.

**Solution.** Validate the service manager, process, socket, and HTTP health response as separate checks. Confirm the listening PID belongs to the expected Guardian command and that the service binds only to the intended interface. Do not terminate the unrelated ARTCB service merely to make the check pass.

Acceptance criteria:
1. systemd reports the expected unit active.
2. Exactly the intended Guardian process owns the expected listener.
3. The health endpoint returns the documented success response.
4. A controlled restart recovers the service and preserves the correct port mapping.
5. The previous `artcb.service` remains stopped only if that is the approved architecture; document the rollback procedure before changing service state.

### 5.2 MCP deployment and actual invocation

**Process.** An MCP client establishes a protocol session, discovers tools, and invokes a tool; the server authorizes the request and returns a result.

**Problem.** A deployed package, process name, or open port does not prove that MCP negotiation, tool discovery, authorization, and an actual tool call succeed. A generic health check also does not prove that TERMINATOR's request path traverses MCP.

**Solution.** Run a minimal authenticated, non-destructive MCP smoke test. Record the protocol/client/server versions, tool name, request correlation ID, result status, and server-side confirmation. Redact tokens and credentials. Test unauthenticated and unauthorized requests as negative cases where supported, without weakening production authorization.

Acceptance criteria:
- MCP initialization succeeds.
- Tool discovery returns the expected allowlisted tools.
- One harmless tool call succeeds and is visible in server-side telemetry.
- Invalid authentication and disallowed tool calls are rejected.
- Timeout and unavailable-server conditions fail closed for protected operations and do not stall the independent defensive decision path.

### 5.3 Doppler and runtime secret injection

**Process.** Doppler supplies a named secret to a process environment or supported secret-injection mechanism at runtime.

**Problem.** A secret existing in a project does not prove that the correct service identity can retrieve it, that the running process received it, or that the deployed code reads the expected variable. Printing environment values into logs would expose the credential.

**Solution.** Verify project/config selection and the expected variable name using metadata and a redacted presence check. Confirm the running process received the variable without displaying its value. Check least-privilege access, rotation procedures, and failure behavior if the secret is absent. Do not paste credentials into reports, terminal transcripts, or Git.

Acceptance criteria:
- Correct Doppler project/config is selected.
- The service's runtime environment contains the required variable name.
- A controlled provider request succeeds without logging the secret.
- Missing or revoked credentials produce a clear, non-secret-bearing error.
- Rotation can be performed without committing secrets or interrupting unrelated services.

### 5.4 ElevenLabs voice functionality

**Process.** Guardian generates narration text, requests speech synthesis, receives audio, and the frontend plays it.

**Problem.** A `voice_enabled: true` flag and a count of configured voices do not prove successful synthesis, correct voice IDs, browser playback, or correct association between narration and a verified security event. Voice generation must not delay or override a defensive decision.

**Solution.** Test the complete chain using a harmless fixed phrase and a real authorized provider request. Verify response status, audio content type/size, browser playback, and the correlation between narration and the source event. Treat the count of four voices as configuration inventory, not proof that all four can synthesize successfully.

Acceptance criteria:
- Each configured voice is tested individually or explicitly marked untested.
- Synthesis failure, timeout, quota exhaustion, or browser autoplay rejection is surfaced.
- Security decisions and event publication continue when voice is unavailable.
- Narration distinguishes observed facts from hypotheses and does not claim a chain or agent was verified beyond the evidence actually checked.
- Provider credentials and raw sensitive user content are not written to logs.

### 5.5 HTTPS, redirect, and frontend integration

**Process.** The HTTP endpoint redirects to HTTPS; TLS authenticates the origin; the browser loads the frontend and connects to the intended API.

**Problem.** A reported 301 does not prove that the redirect target is correct, that TLS is valid, or that the frontend API requests succeed. A rendered 3D interface can be static or animated without consuming live backend events.

**Solution.** Validate the redirect status and `Location` header, TLS hostname/certificate/expiry, browser console, network responses, and the live data path. Confirm the frontend uses the intended API base URL and that CORS, cookies, or authorization settings do not silently prevent requests.

Acceptance criteria:
- HTTP returns the intended permanent redirect to HTTPS.
- HTTPS certificate and hostname validation succeed.
- No redirect loop or mixed-content failure occurs.
- The frontend receives an identifiable live Guardian event.
- The event changes the expected UI state, and an API outage is visibly represented rather than mistaken for a live system.

### 5.6 KYC, defensive decisions, and forensic evidence

**Process.** A KYC scenario produces identity-check events, simulated or real attack signals, Guardian decisions, evidence-chain verification, and a final result.

**Problem.** A KYC verdict of `APPROVED` is not by itself a security certification. A scenario may be synthetic; a demonstration can report an attack blocked while the final KYC workflow approves the subject. These may be logically compatible, but the event semantics and test fixture must be explicit. R066 itself documents a synthetic/demo path and explicitly leaves full certification and unique-human proof false.

**Solution.** Label simulated fixtures and live provider-backed checks distinctly. Test both expected approval and rejection paths, including an attack blocked without corrupting the business outcome. Independently validate evidence-chain tamper detection: intact evidence must pass; altered evidence must fail; missing events must be reported as incomplete, not silently treated as valid.

Acceptance criteria:
- Synthetic versus production evidence is unambiguous.
- Each security decision links to its input event, policy/rule version, and evidence.
- Chain verification covers exactly the stated events and states its limits.
- Alteration, omission, replay, and out-of-order events are tested.
- `CERTIFIED_100=false` and `unique_human_proven=false` remain explicit until separately evidenced and approved.

## 6. Prioritized remediation plan

### P0 — Establish current production truth
1. Capture UTC timestamp, deployment commit/version, host identity, and sanitized service status.
2. Verify `artcb.service` and `artcb-guardian.service` states independently.
3. Verify the port 8002 listener and health endpoint.
4. Test HTTPS redirect and TLS from an external client.
5. Do not report PASS based solely on configuration flags or a previous session.

### P0 — Prove the real request path
1. Perform one authorized MCP initialize, tool-discovery, and harmless tool-call sequence.
2. Correlate client request, Guardian server event, and result.
3. Perform one harmless ElevenLabs synthesis request and verify frontend playback.
4. Confirm voice failures cannot delay Guardian decisions.

### P1 — Test recovery and failure modes
1. Restart Guardian in a controlled maintenance window and verify recovery.
2. Simulate provider timeout, invalid credentials, and quota/unavailability without exposing secrets.
3. Verify the frontend indicates degraded state when API or audio is unavailable.
4. Check service logs for secret leakage, unbounded sensitive payloads, and misleading success messages.

### P1 — Certify forensic correctness
1. Re-run intact-chain and tampered-chain tests.
2. Validate event ordering, missing-event handling, correlation IDs, and evidence provenance.
3. Separate synthetic KYC demonstrations from production KYC claims.
4. Preserve original forensic evidence and record test artifacts by hash; do not commit raw logs.

### P2 — Improve operational readiness
1. Add documented readiness and liveness checks.
2. Define alerting for repeated restarts, MCP failures, voice-provider errors, TLS expiry, and missing event flow.
3. Document rollback and recovery steps.
4. Publish a release acceptance matrix with owner, command/test, expected result, evidence reference, and timestamp.

## 7. Security and change-control observations

- Do not place secret values, authorization headers, raw identity documents, or unredacted production logs in Git.
- Keep logs and evidence in the approved operational evidence store; this report contains no runtime logs.
- Do not grant blanket root/admin privileges to agents as a substitute for explicit, auditable authorization. Autonomous remediation should use scoped service identities and narrowly defined actions, with emergency actions logged and reversible.
- Do not disable unrelated ARTCB services merely to clear a port conflict.
- Do not change deployment state based only on this documentation audit.
- No change was made to the separate `vgactech/artcb` repository or to any VLC&ARTCB project.

## 8. Final assessment

The supplied R070 summary describes a plausible deployment state, but the current audit cannot independently certify the OVH2 service state, MCP operation, Doppler injection, ElevenLabs synthesis, or browser-level integration. The latest repository-visible R066 evidence is useful but explicitly retains debug and non-certification caveats.

**Release decision: HOLD production certification pending the P0 evidence above.** This is not a claim that the deployment is down; it means that the evidence available to this audit is insufficient to certify it as healthy and fully operational.

The next report should record each live test with UTC timestamp, exact command or request, sanitized output, deployed commit, and PASS/FAIL/NOT RUN status. Keep secrets and raw logs outside the Git repository.
