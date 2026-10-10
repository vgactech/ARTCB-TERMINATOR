# R043 — Operational Readiness, Two-Server Live Validation, and KYC Evidence Plan

**Date:** 2026-10-10  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Branch:** `main`  
**Baseline observed:** `7be4d72f264b29e405c48ab272179e328ee5d042` (R042)  
**Scope:** Report-only. No application code, deployment configuration, secrets, or runtime logs are modified by this report.

## Expertises activated

- Operational readiness and release engineering
- API integration and distributed-system observability
- KYC workflow validation and evidence-based assurance
- AI-agent security and controlled adversarial testing
- Secrets management, Doppler, and AWS STS lifecycle
- MCP, frontend integration, and end-to-end testing
- Forensic event provenance and audit evidence
- GitHub repository governance

## Executive decision

**Current status: NOT YET PROVEN READY for a full two-server live KYC demonstration.**

R042 records useful component-level evidence, including a Guardian health response, a confirmed HTTP 503 when `GUARDIAN_ATTACKER_ENABLED=false`, an MCP initialization/ping check, a successful frontend build, and 209/209 reported tests observed during that session. However, R042 does not establish that both server environments were simultaneously reachable, integrated, and successfully executing the complete validated KYC scenario end to end.

This is an evidence gap, not proof that the KYC scenario is absent or that the servers are not operational. The KYC scenario may already exist and may have been validated previously; this report requires its existing evidence to be located and re-verified rather than rebuilding or silently replacing it.

## 1. Evidence observed in R042

| Area | Reported observation | Operational conclusion |
|---|---|---|
| Secrets | Required keys present; empty `GUARDIAN_FRONTEND_ORIGIN`; temporary AWS STS token nearing expiry | Configuration findings remain open until safely verified in Doppler |
| Guardian API | Health response `status=ok`; attacker-disabled path returns HTTP 503 | Individual endpoint behavior observed; full cross-server workflow not established |
| ARTCB API | Check blocked by missing Windows `fcntl`; OVH unavailable/offline | Target Linux/OVH behavior remains unverified by this check |
| MCP | 12 tools; initialize and ping work; unknown method returns expected `-32601` | Basic protocol behavior observed; business workflow integration remains unproven |
| Frontend | Build completed, no TypeScript errors reported, no vulnerabilities reported by that run; proxy targets port 8000 | Build success is not browser-to-backend end-to-end evidence |
| Tests | 164 Python + 45 Rust = 209/209 PASS reported as directly observed | Passing tests do not automatically prove live KYC or deployment readiness |

## 2. Immediate orders

### P0 — Establish the actual environment and KYC evidence

1. Identify the exact URLs, deployment identifiers, regions, and versions of both live server environments. Do not infer that a local process is the live service.
2. Locate the already validated KYC scenario, its test definition, expected outputs, test account/data classification, and prior execution evidence.
3. Record whether the KYC validation is a unit, integration, staging, or production test. These labels are not interchangeable.
4. Re-run the approved KYC scenario only in the designated test environment and with synthetic or explicitly authorized test identities. Do not use real identity documents or production personal data merely to demonstrate functionality.
5. Capture timestamped request/response evidence, correlation IDs, deployment/build identifiers, and the final workflow state. Redact tokens, credentials, identity attributes, and other sensitive data.
6. If the KYC scenario depends on an external provider, record provider sandbox/live mode and the provider-side transaction or correlation reference, without storing secrets or unnecessary personal data.

**Pass condition:** a reproducible end-to-end run proves that the frontend/orchestrator reaches the intended server, that the KYC workflow reaches its expected terminal state, and that the relevant events are correlated across both servers. Any unavailable layer must be marked NOT VERIFIED, not PASS.

### P0 — Resolve configuration findings safely

1. Set `GUARDIAN_FRONTEND_ORIGIN` in the correct Doppler project/configuration to the exact authorized frontend origin for the target environment. Confirm CORS behavior from the actual browser origin.
2. Refresh the expiring AWS STS session through the approved identity/provider flow. Verify expiration metadata and permissions without printing or copying credentials into chat, reports, commits, or logs.
3. Confirm that the service uses the intended AWS role and only the permissions required for its declared runtime tasks. Do not broaden permissions as a workaround for a failed deployment.
4. Validate required environment variables at startup; fail closed for security-critical missing configuration and emit a sanitized diagnostic.
5. Ensure secrets are absent from Git history, build artifacts, frontend bundles, crash traces, and test output. If a real secret was ever committed or exposed, rotate/revoke it; labelling a value as fake must be supported by verification.

**Pass condition:** the target environment starts with the intended configuration, the frontend origin is exact, credentials are valid, and no secret value is exposed in evidence.

### P0 — Verify both servers from the target runtime

1. Run the ARTCB API check on the actual supported Linux runtime (or its real OVH target), not on Windows if the implementation requires `fcntl`.
2. Restore/reach the intended OVH environment and capture the deployed revision, service health, dependency health, and timestamps.
3. From the actual frontend origin, exercise the complete request path through the configured proxy and verify the response from the intended backend.
4. Test Guardian and ARTCB together with correlation IDs. Verify that an outage or timeout in one server is surfaced as a dependency failure rather than misreported as an overall success.
5. Repeat the check after any configuration refresh or deployment; do not reuse an earlier health response as evidence for the current runtime.

**Pass condition:** both endpoints are independently reachable and their integration path succeeds from the designated test client in the same validation window.

### P1 — Validate the defense and evidence chain

1. Run the approved controlled attack scenario in an isolated test environment, with the attacker feature disabled by default and enabled only for the test window.
2. Verify the complete sequence: input → agent/tool activity → detection → policy decision → containment/block → evidence capture → replay/reconstruction → final verification.
3. Distinguish attempted, detected, blocked, successful, and unknown outcomes. A 503 response when the attacker is disabled proves that specific guard path, not the whole defensive workflow.
4. Verify that event IDs, timestamps, source identities, policy/version identifiers, and causal parent-child links persist across both servers.
5. Verify that missing telemetry, delayed events, and failed evidence writes are visible and cannot silently produce a green result.
6. Confirm that voice narration, frontend visualization, or other optional features cannot delay or bypass the enforcement decision.

**Pass condition:** the controlled scenario produces a replayable evidence package and independently checkable results, with no unsupported claim of complete coverage.

### P1 — Confirm test scope and release gate

1. Preserve the R042 baseline of 209/209 tests as a historical observation, but record the exact command, commit, platform, and output for each new run.
2. Add or execute tests specifically covering two-server integration, the KYC happy path, invalid/expired KYC input, provider timeout, duplicate submission/idempotency, authorization failure, and sanitized error handling, where these cases are supported by the existing design.
3. Report test counts by category; do not equate unit-test success with production validation.
4. Run frontend/browser tests against the actual API path, not only a compile/build command.
5. Keep the known Windows `fcntl` limitation explicit and separately validate the supported Linux deployment.

**Release gate:** no claim of “live KYC validated end to end” until the corresponding evidence is available and current.

## 3. Additional requirements that are easy to overlook

- **Environment identity:** label local, CI, development, staging, and production separately.
- **Version pinning:** include commit SHA, image/build digest, configuration version, and relevant model/policy versions in the evidence bundle.
- **Time and correlation:** retain event time and ingestion time, timezone, request/trace ID, and cross-service correlation IDs.
- **Data protection:** use synthetic or authorized test identities; redact personal data and secrets; set retention and access rules for KYC evidence.
- **Idempotency and retries:** prove that a retry cannot create duplicate KYC decisions or inconsistent states.
- **Failure behavior:** test timeouts, partial outages, stale STS credentials, provider errors, and unavailable telemetry.
- **Rollback and recovery:** document the last known-good revision and the safe rollback procedure before changing a live deployment.
- **Observability:** ensure health checks are supplemented by dependency/readiness checks and one real synthetic workflow.
- **Evidence integrity:** hash or sign sanitized evidence artifacts and preserve the source of each assertion.
- **No false green status:** an untested layer, unreachable host, missing log, or inconclusive provider result must be reported as NOT VERIFIED or BLOCKED.
- **No log commits:** never commit raw runtime logs, request payloads, KYC documents, access tokens, or credential-bearing environment dumps to the repository.
- **No cross-project migration:** do not import, migrate, or integrate anything from VLC&ARTCB without an explicit instruction.

## 4. Autonomy and permissions

Operational autonomy should mean that agents can diagnose, gather approved telemetry, run predefined tests, prepare a patch/report, and recommend or perform reversible actions within a declared scope. It should not mean unrestricted root/admin access across every host, unrestricted access to KYC personal data, or permission to rotate credentials and alter production state without a defined authorization path.

Use short-lived credentials, narrowly scoped service identities, explicit environment boundaries, and auditable execution. This improves independent operation while limiting the impact of a compromised or mistaken agent. Emergency automation can be pre-authorized for specific reversible actions, with a recorded policy and a recovery path.

## 5. Required evidence checklist

- [ ] Current deployed revision and environment identity for Guardian
- [ ] Current deployed revision and environment identity for ARTCB/OVH
- [ ] Guardian health and readiness checks from the target client
- [ ] ARTCB health and readiness checks from the supported Linux runtime
- [ ] Frontend-origin/CORS and proxy-path verification
- [ ] Existing KYC scenario definition and its acceptance criteria
- [ ] Timestamped end-to-end KYC run with correlation IDs
- [ ] Provider mode (sandbox/live) and sanitized provider reference
- [ ] Invalid-input, timeout, retry/idempotency, and authorization-failure results
- [ ] Controlled defense test with detection, containment, and replay evidence
- [ ] Current automated test outputs linked to the exact commit
- [ ] Confirmation that logs and secrets were not committed
- [ ] Rollback target and recovery procedure

## 6. Final status model

Use one of these explicit statuses per check:

- **PASS — VERIFIED:** direct, reproducible evidence exists for the stated scope.
- **FAIL — VERIFIED:** the check ran and the expected condition was not met.
- **BLOCKED:** the check could not run because a dependency, host, permission, or environment was unavailable.
- **NOT VERIFIED:** the necessary evidence is not available in the audit record.
- **NOT APPLICABLE:** the control does not apply, with a documented reason.

Do not label the entire system operational based solely on component health checks.

## Final recommendation

**Order of execution: P0 environment/KYC evidence inventory → P0 Doppler origin and STS remediation → P0 target-runtime two-server validation → P1 controlled defense/replay validation → P1 release gate.**

The first deliverable is a factual status matrix backed by current evidence, not a code migration. All work under this report is documentation and validation planning; no application code or runtime configuration is changed by this report.
