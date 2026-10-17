# R082 — Critical Audit of R082 Consolidated Status and KYC URL Remediation Claims

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Latest repository head inspected:** `c1632db097b6a7414e7ed027d02b4d9f22c6fa35`  
**Technical commit inspected:** `f2e1c8551a02b9d97f274d138deffad71db24bcc`  
**Previous audit inspected:** `c1632db097b6a7414e7ed027d02b4d9f22c6fa35` (R081)  
**Scope:** Read-only repository audit. Current `main` source files and the R080/R081 commits were inspected through GitHub. No production requests, server commands, test suites, provider dashboards, DNS queries, or cloud hosts were independently tested. This report is the only intended repository change.

**Required invariants:** `CERTIFIED_100=false`; `unique_human_proven=false`.

## 1. Executive conclusion

The supplied R082 summary contains useful operational information, but its most important new remediation claim is **contradicted by the current repository source**.

The summary says `start_guardian.sh` was changed to POST synthetic KYC data to `/api/demo/start`, removing personal fields from the URL. However, the current `main` version of `start_guardian.sh` still calls:

`/api/kyc/stream?first_name=Alice&last_name=Martin&doc_id=TEST-001&dob=1990-01-01`

This is a confirmed source-level discrepancy. The claimed fix is not present in the inspected repository head. No code was changed during this audit.

R081's earlier finding also remains relevant: changing `/api/demo/start` to accept a POST body does not remove the legacy query parameters from that endpoint or the KYC fields accepted by `GET /api/kyc/stream`. A complete privacy remediation therefore cannot be marked done.

The reported DNS, HTTPS, public SSE, rate-limit, voice-provider, blockchain-node health, and isolation states were not independently retested in this read-only audit. They remain **reported operational claims**, not newly verified results.

## 2. Expertise activated

- GitHub repository and commit-history verification
- Application security and privacy engineering
- FastAPI request semantics and Server-Sent Events
- KYC data minimisation and URL/log exposure
- Rate limiting behind reverse proxies
- AI-provider mode and fallback verification
- SSH host authentication and deployment hardening
- Evidence quality, test design, and operational readiness

## 3. Findings: process, problem, correction

### P0 — R082 claims a KYC script correction that is absent from current `main`

**Process — what should happen:** The smoke test should send synthetic KYC values in a JSON POST body to the intended demo endpoint, or create a short-lived session using a POST body and then open an SSE stream with only an opaque, non-sensitive session identifier.

**Evidence:** The current `start_guardian.sh` fetched from `main` still performs a GET request to `/api/kyc/stream` with `first_name`, `last_name`, `doc_id`, and `dob` in the query string.

**Problem — why it matters:** Query strings can be captured by Nginx and application access logs, monitoring systems, tracing tools, and intermediary infrastructure. HTTPS protects the connection in transit; it does not prevent endpoints from logging the URL. Although the values shown in the smoke test are synthetic, the script normalises a risky pattern and can later be copied with real values.

**Correction:**
1. Update `start_guardian.sh` in a separate, explicitly authorised implementation change; this audit does not change application files.
2. Use the POST-body flow consistently and confirm the response contract. Do not assume `/api/demo/start` and `/api/kyc/stream` are interchangeable endpoints.
3. Remove identity-bearing query parameters from the API contract after client migration, rather than merely documenting them as deprecated.
4. Add a regression test that asserts the request URL contains none of the KYC fields and that captured access logs do not contain synthetic test values.
5. Verify that the script's expected response/event shape matches the endpoint it actually calls.

**Status:** Confirmed discrepancy between R082's stated correction and the current repository source. The fix is not present in the inspected `main` file.

### P1 — KYC query parameters remain supported in the API

**Process:** The technical commit `f2e1c85` added a Pydantic request model to `POST /api/demo/start`, but retained legacy query parameters for backward compatibility. The current source also exposes `GET /api/kyc/stream` with KYC identity fields as query parameters.

**Problem:** A safer request path exists, but unsafe alternatives remain callable. Therefore “KYC POST body supported” is true; “KYC data is no longer sent in URLs” is not established.

**Correction:** Migrate callers, then reject or remove identity-bearing query parameters. Add tests for both endpoints, inspect proxy logging configuration, and document the cutover. If an SSE GET is required by the browser's EventSource API, create a session via POST first and pass only a random, short-lived, revocable opaque identifier to the stream URL.

**Status:** Confirmed from current source and R081 evidence.

### P1 — `llm_mode: "fallback"` is observability, not proof of a successful live LLM

**Process:** The SSE payload reports a backend label obtained from the attacker result. This helps distinguish the code path taken.

**Problem:** A fallback label is evidence that the reported run used a fallback path; it does not prove OpenRouter or another live provider succeeded. The R082 task “test `llm_mode: "openai"` via OpenRouter” is still outstanding. The inspected `llm_attacker.py` documents OpenAI/Bedrock selection, but provider configuration and a successful live request were not exercised in this audit.

**Correction:** Run an explicit acceptance test against the configured provider, capture redacted provider/model metadata and a correlation ID, and fail the live-provider test if a deterministic fallback is returned. Keep provider secrets and raw sensitive payloads out of the evidence.

**Status:** Live provider use not independently verified.

### P1 — Rate-limit code exists, but production enforcement is not proven

**Process:** `f2e1c85` adds SlowAPI limits, including `6/minute` on `POST /api/llm-attack/stream` and `10/minute` on `POST /api/demo/start`.

**Problem:** Source annotations do not prove the effective limits behind Nginx. The limiter uses `get_remote_address`; if the ASGI peer address is the reverse proxy, many users may share a quota unless trusted-proxy handling is correctly configured. Conversely, arbitrary forwarded headers must not be trusted.

**Correction:** Verify the actual ASGI client address through the live proxy chain; configure only known proxy hops as trusted; test independent clients and confirm that one client cannot exhaust another's quota. Add concurrency, maximum-duration, timeout, and provider-spend controls for expensive routes.

**Status:** Code addition confirmed; live enforcement not independently verified.

### P1 — SSH `accept-new` is an improvement, not prior host-key verification

**Process:** SSH accepts a previously unseen host key and rejects a changed key on later connections.

**Problem:** On first connection, the key is trusted without independent verification. This does not satisfy the separate R082 task to verify the OVH2 host key beforehand.

**Correction:** Obtain the expected host key/fingerprint through a trusted channel, pin it in a managed `known_hosts` file, and test that a mismatched key prevents both file transfer and remote commands.

**Status:** The option change is confirmed in `f2e1c85`; prior host-key verification remains outstanding.

### P1 — Bootstrap configuration and Dependabot tasks are not resolved by the inspected evidence

**Process:** The supplied summary lists removal of `151.80.107.29:8000` from `BOOTSTRAP_NODES` and three Dependabot alerts.

**Problem:** A root-level `config.py` fetch returned 404, so that path is not present at repository root on the inspected ref. This does not prove that the value is absent elsewhere. Dependabot alerts cannot be confirmed from the inspected code diff alone.

**Correction:**
1. Locate the actual definition of `BOOTSTRAP_NODES` in the repository before proposing a change; verify whether the IP is still required and identify the intended replacement/retirement process.
2. Inspect the repository's live Dependabot alerts and match each advisory to its dependency, affected version, and remediation version.
3. Do not claim either task complete until the relevant source or alert record is examined.

**Status:** Both remain unverified in this audit.

### P1 — Frontend controls and live service claims remain unverified

**Process:** A source-level frontend review identifies controls and their handlers; an end-to-end test confirms that each control reaches the expected backend behaviour in a real browser.

**Problem:** R082 lists a frontend button audit as outstanding. The supplied summary also reports public HTTPS, 13 SSE events, blockchain health, and node isolation, but this audit did not make external requests or inspect the live nodes.

**Correction:** Test each frontend control in a controlled environment; capture request/response correlation and expected UI state. Separately rerun HTTPS, SSE sequence/order, rate-limit, voice, and isolation checks from an external runner. Record timestamps, target environment, observed results, and limitations, with secrets and PII redacted.

**Status:** No fresh runtime confirmation.

## 4. R082 task register — updated audit status

| Task | Priority | Audit status | Next evidence required |
|---|---|---|---|
| Live LLM through OpenRouter | P1 | Outstanding | Successful live-provider acceptance test, explicitly excluding fallback |
| Remove `151.80.107.29:8000` from `BOOTSTRAP_NODES` | P1 | Unverified | Locate actual config definition and verify intended node retirement |
| Dependabot alerts (high/moderate/low) | P1 | Unverified | Inspect each live advisory and affected dependency |
| React frontend button audit | P1 | Outstanding | Button-by-button browser test with backend correlation |
| OVH2 SSH host-key pre-verification | P2 | Outstanding | Trusted fingerprint plus mismatch rejection test |
| Deployment script relative-path portability | P2 | Outstanding | Path/configuration review and clean-environment dry run |
| `start_guardian.sh` KYC URL removal | P0 | **Not fixed in inspected `main`** | Update script and add URL/log regression tests |
| Voice isolation from Guardian decisions | P0 | Prior R081 finding remains open in inspected source | Blocked-TTS regression test proving security events progress independently |

## 5. Acceptance gates

Do not mark the release “100% certified” based on a successful demo alone. At minimum:

1. The KYC smoke test contains no identity-bearing query string.
2. The legacy KYC query paths are removed or explicitly rejected after migration.
3. A blocked voice provider cannot delay Guardian security decisions or chain-verification events.
4. A live-LLM test proves provider success and cannot silently pass through fallback.
5. Rate limits are validated through the real proxy with distinct clients.
6. SSH rejects an unexpected first-use host key.
7. Frontend and public-service claims have reproducible, timestamped evidence.
8. The invariants remain `CERTIFIED_100=false` and `unique_human_proven=false` until independently justified.

## 6. Scope and non-actions

- Inspected current `main` source for `start_guardian.sh`, `guardian_api/app.py`, and `guardian_mcp/llm_attacker.py), along with commits `f2e1c85`, `bcfbabb`, and `c1632db`.
- Did not run application code, execute tests, call production endpoints, access cloud hosts, query Doppler, or inspect provider dashboards.
- Did not change application code, tests, deployment scripts, configuration, secrets, or runtime logs.
- No logs or secrets were added to the repository.
- This report is the only intended change from this audit.
