# R081 — Critical Audit of Commit bcfbabb and R080 Remediation Claims

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Documentation commit audited:** `bcfbabbc3057ad4a9354e48bd287cbe260818e4d`  
**Technical fix commit reviewed:** `f2e1c8551a02b9d97f274d138deffad71db24bcc`  
**Scope:** Read-only review of the documentation commit, its referenced code commit, and current `main` versions of `guardian_api/app.py`, `guardian_api/requirements.txt`, `guardian_mcp/llm_attacker.py`, `start_guardian.sh`, and `deploy_terminator_ovh2.sh`. No runtime calls, production tests, or test suite were executed independently. No application code, configuration, secrets, logs, or deployment targets were changed.

**Invariant status:** `CERTIFIED_100=false`; `unique_human_proven=false`. Do not change either invariant without independent evidence.

## 1. Executive conclusion

Commit `bcfbabb` adds R080 documentation; the underlying code changes are in `f2e1c85`. The technical commit improves the implementation by adding explicit rate limits to two routes, adding an `llm_mode` field to the SSE attack event, accepting a Pydantic request body on `/api/demo/start`, and changing SSH host-key behaviour from `StrictHostKeyChecking=no` to `accept-new`.

**The remediation is partial, not complete.** The current source still has synchronous voice-provider calls inside the SSE generator, KYC identity fields in a GET URL in `start_guardian.sh`, a GET endpoint that accepts KYC fields as query parameters, and SSH first-use trust that is not equivalent to a pre-verified host key. The LLM mode is exposed in the SSE event, but this does not prove that a live model was used. Reported production checks remain unverified by this read-only audit.

## 2. Expertise activated

- Application security and API threat modelling
- FastAPI, Python, SlowAPI, reverse-proxy behaviour, and Server-Sent Events
- AI agent orchestration and live-provider versus deterministic-fallback validation
- Privacy engineering and personal-data minimisation
- SSH host authentication and deployment hardening
- Reliability engineering, test design, and evidence integrity
- Git history and repository auditability

## 3. Findings

### P0-1 — Voice synthesis still blocks the SSE generator

**Evidence:** In current `guardian_api/app.py`, `_sse_generator()` calls `yield from _emit_voice(...)` after `session_opened`, `attack_generated`, and `propagation`. `_emit_voice()` yields `voice_script`, then synchronously calls `vc.speak_commentator()` or `vc.speak_agent()` before it can return. Similar calls occur after `guardian_decision`.

**Process — what happens:** Yielding an SSE message does not terminate the generator. The generator resumes and executes subsequent statements. A synchronous voice call blocks that generator until the provider returns or fails.

**Problem — why it matters:** The security decision is emitted before the voice call associated with that decision, but voice synthesis for earlier stages can still delay attack generation, propagation, and arrival of the decision itself. The code comments claim audio latency never delays the security pipeline, but the control flow does not support that broad claim.

**Correction:**
1. Move TTS calls to a bounded asynchronous worker or queue that is independent from the security pipeline.
2. Emit decision and chain-verification events without waiting for audio generation.
3. Set provider timeouts and cancellation behaviour; bound queue size and record late/dropped audio without logging secrets.
4. Add a regression test with a TTS test double that blocks indefinitely. The decision and chain-verification events must still arrive within the agreed latency budget.

**Acceptance criterion:** With TTS deliberately blocked, security events still complete on time; only narration/audio may be delayed or omitted.

**Status:** Confirmed source-code finding. No live latency measurement was performed.

### P0-2 — Rate limiting is an improvement, but the effective client identity must be validated

**Evidence:** The technical commit adds SlowAPI, configures `Limiter(key_func=get_remote_address, default_limits=["60/minute"])`, and decorates `POST /api/llm-attack/stream` with `6/minute` and `POST /api/demo/start` with `10/minute`. The code also has expensive routes such as `POST /api/llm-attack/run` and `POST /api/simulation/run`.

**Process:** A limiter counts requests under the identity returned by its key function. Here the key function uses the client address observed by the ASGI request.

**Problem:** When Nginx proxies traffic to Uvicorn, the ASGI peer address may be the proxy address, rather than the original visitor. If so, distinct users can share a quota. Conversely, forwarded headers must not be trusted indiscriminately, because an untrusted client may spoof them. The source code alone does not establish what Uvicorn proxy-header trust settings are active in production. The explicit route limits also do not establish that concurrency, maximum stream duration, provider spend, and request timeouts are controlled.

**Correction:**
1. Verify the actual ASGI client address through the production proxy chain.
2. Configure trusted proxy handling narrowly for known proxy hops; never trust arbitrary forwarded headers.
3. Add authenticated per-identity quotas, concurrent-run caps, maximum SSE duration, provider timeouts, and budget safeguards.
4. Test requests from multiple client IPs through the real proxy and verify that one client cannot exhaust another client's quota.
5. Test the effective limits on `/api/llm-attack/run`, `/api/simulation/run`, `/api/llm-attack/stream`, and `/api/demo/start` individually.

**Status:** Rate-limiting code additions confirmed. Effective production enforcement and client-IP correctness are not independently verified.

### P1-1 — KYC data is not removed from URLs across the complete workflow

**Evidence:** The updated `/api/demo/start` accepts a `KYCStartBody`, but also retains `scenario_id`, `first_name`, `last_name`, `doc_id`, and `dob` as query parameters for compatibility. In the current `start_guardian.sh`, the smoke test still calls `/api/kyc/stream?first_name=Alice&last_name=Martin&doc_id=TEST-001&dob=1990-01-01`. Current `guardian_api/app.py` also defines `GET /api/kyc/stream` with these identity fields as query parameters.

**Process:** Query strings can be recorded by reverse-proxy access logs, server logs, monitoring, tracing, browser history, and other intermediaries. HTTPS encrypts transport but does not prevent the endpoints or proxies from logging the URL.

**Problem:** Adding a POST body to one route does not remove exposure in other routes and scripts. The old query-parameter path remains usable, and the current start script continues to demonstrate the risky pattern.

**Correction:**
1. Migrate the KYC stream to a POST request with a validated body, or use a protected POST to create a short-lived session followed by a stream URL containing only an opaque non-sensitive identifier.
2. Update `start_guardian.sh` to use the new workflow.
3. Deprecate and then remove PII-bearing query parameters; do not merely describe them as deprecated without enforcing the transition.
4. Redact identity fields in access logs and telemetry.
5. Add tests that assert names, document identifiers, and dates of birth never appear in request URLs or captured logs.

**Status:** Confirmed in current repository source. Use of real personal data in production is not established.

### P1-2 — SSH `accept-new` is safer than `no`, but it is not host-key pinning

**Evidence:** The deployment script replaces `StrictHostKeyChecking=no` with `StrictHostKeyChecking=accept-new` for SSH and SCP.

**Process:** `accept-new` accepts a host key that has not previously been seen and rejects a changed key on later connections.

**Problem:** The first connection still trusts whichever host key is presented. If that initial connection is intercepted or directed to the wrong host, the unexpected key can be recorded as trusted. This is an improvement over disabling checking, but it is not equivalent to verifying a known host key obtained through a trusted channel.

**Correction:**
1. Pin the expected OVH2 host key or manage a verified `known_hosts` file.
2. Fail closed if the host key does not match the independently verified value.
3. Keep deployment credentials in a protected credential mechanism and use a dedicated deployment identity.
4. Test the script with a deliberately mismatched host key and confirm that no copy or remote command occurs.

**Status:** The SSH option change is confirmed. Independent host-key verification is not demonstrated.

### P1-3 — `llm_mode` improves transparency but does not prove live LLM execution

**Evidence:** The SSE `attack_generated` payload now includes `llm_mode: llm_result.get("backend", "unknown")`. Current `guardian_mcp/llm_attacker.py` returns backend `openai` when the OpenAI-compatible call succeeds and `fallback` when no key is available or the call raises an exception. The fallback returns a deterministic `wallet.sign` request to `simulated-attack.invalid`. The module documentation still describes Bedrock as the fallback, but the current `_call_llm()` path falls back deterministically and does not call `_invoke_bedrock()`.

**Process:** A backend label reports which branch the implementation says it took. It is useful for distinguishing a deterministic fixture from a provider response.

**Problem:** A displayed `openai` label alone is not a complete audit record of the provider, model, endpoint, response identifier, and successful tool-call parsing. R080 lists `bedrock` as a possible mode, but the current main-path selection code does not use Bedrock. The non-streaming `/api/llm-attack/run` response includes the model in its attacker object but does not include the same backend field there. The report's statement that the event label lets the jury know the mode is useful, but it does not prove that a particular production run used a live LLM.

**Correction:**
1. Expose a consistent backend/mode field in both streaming and non-streaming responses.
2. Use explicit states such as `LIVE_PROVIDER`, `DETERMINISTIC_FALLBACK`, and `SIMULATION`.
3. Include redacted provider metadata and a request/response correlation ID in the audit record; never include API keys.
4. Make a live-LLM acceptance test fail if the provider call fails or a fallback is used.
5. Correct the stale Bedrock fallback documentation, or implement and test that path deliberately.

**Status:** Mode-label code confirmed. A successful live-provider run was not independently performed.

### P1-4 — Deployment script remains machine-specific and does not itself configure HTTPS

**Evidence:** `deploy_terminator_ovh2.sh` hardcodes local paths under `/Users/deyi/.bob/` and uses a remote Nginx server block listening on port 80. The script writes the configuration before running `nginx -t`, then reloads Nginx.

**Process:** The script copies local frontend/API artifacts, installs requirements, writes a Nginx configuration, tests the active Nginx configuration, and reloads the service.

**Problem:** The hardcoded workstation paths reduce reproducibility. The script itself does not configure TLS in the server block it writes. A separate pre-existing Nginx configuration or external TLS terminator might provide HTTPS, but that must be checked independently. Writing a candidate configuration before validation also makes rollback and recovery less safe.

**Correction:**
1. Make local artifact paths configurable and validate all required inputs before connecting.
2. Stage candidate Nginx configuration, validate it before installation, then install atomically.
3. Back up the active configuration and define rollback behaviour.
4. Verify the public certificate chain, hostname, redirects, API routing, and SSE buffering independently after deployment.
5. Make success output distinguish copied files from externally verified service health.

**Status:** Source finding confirmed. Current public TLS behaviour was not tested.

### P1-5 — R080 records claims that exceed what this audit independently establishes

**Evidence:** R080 states that public DNS, HTTPS, API health, the 13-event SSE sequence, HTTP 429 after the seventh request, ElevenLabs key configuration, and node isolation are operational. The commit itself adds documentation; it does not contain independent evidence that these conditions remain true at audit time.

**Process:** A report can record test observations, but its statements are only as reproducible as the underlying test artefacts and environment details.

**Problem:** This read-only audit did not execute public requests, test the production limiter, inspect provider dashboards, or query the OVH/AWS nodes. Therefore those claims must be classified as reported, not independently verified. Also, R080 says prior reports R065–R079 were preserved; this report should be included in the continuing sequence without rewriting previous reports.

**Correction:**
1. Attach redacted automated test output with timestamps, target environment, request count, HTTP status, SSE event order, and completion time.
2. Keep live-provider verification distinct from fallback success.
3. Repeat external HTTPS, SSE, rate-limit, and node-isolation tests from a controlled external runner.
4. Never commit logs containing secrets, personal data, API keys, or raw provider payloads.

**Status:** Claims recorded in repository; not independently verified by this audit.

## 4. Status against R080's remediation checklist

| Item | Audit status | Required next action |
|---|---|---|
| Voice SSE asynchronous | Not implemented in inspected source | Separate bounded voice worker and blocked-TTS regression test |
| Real LLM through OpenRouter | Not proven | Run a live-provider acceptance test and record redacted evidence |
| Remove OVH2 from bootstrap nodes | Not verified; claimed path `config.py` is not at repository root | Locate the actual configuration file, inspect it, and verify redeployment separately |
| Dependabot alerts | Not verified in this source audit | Inspect repository security alerts through GitHub and remediate the actual advisory |
| Frontend React button-by-button audit | Not performed in this scope | Identify the frontend source and exercise each control against a test environment |
| KYC URL parameters in `start_guardian.sh` | Still present | Replace with the approved POST/session workflow |

## 5. Prioritised action plan

1. **P0:** Decouple voice synthesis from the security-event generator.
2. **P1:** Remove PII from every KYC URL path, including `/api/kyc/stream` and `start_guardian.sh`.
3. **P1:** Validate per-client rate limiting behind the production reverse proxy; add concurrency and duration limits.
4. **P1:** Verify SSH host keys through a trusted channel rather than trusting the first observed key.
5. **P1:** Standardise and independently prove live-LLM versus fallback mode across all API paths.
6. **P1:** Make deployment staging, TLS verification, and rollback reproducible.
7. **P1:** Collect repeatable external evidence for all production claims in R080.

## 6. Scope and non-actions

- Reviewed the R080 document and the referenced technical commit, plus current source files on `main`.
- Did not run the application, call public production endpoints, execute a test suite, query cloud nodes, or inspect private secret stores.
- Did not modify application code, configuration, secrets, deployment targets, or runtime logs.
- This report is intended as the only repository change from this audit.
- Keep `CERTIFIED_100=false` and `unique_human_proven=false` unless independent evidence supports a change.
