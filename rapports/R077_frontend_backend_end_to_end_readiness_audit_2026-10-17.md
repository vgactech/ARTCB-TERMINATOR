# R077 — Frontend-to-Backend Operational Readiness Audit and End-to-End Acceptance Plan

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Scope:** Read-only review of repository-visible frontend/API integration and the user-provided R076 infrastructure status claims.  
**Change policy:** Report-only. No application code, tests, deployment configuration, DNS, infrastructure, secrets, logs, or other repository was modified.

## 1. Executive assessment

**Status: PARTIALLY IMPLEMENTED; END-TO-END PRODUCTION READINESS NOT INDEPENDENTLY CERTIFIED.**

The repository contains a React/TypeScript frontend, a FastAPI backend, a frontend API client, scenario orchestration, and Server-Sent Events (SSE) components. This establishes that the principal software pieces exist. It does not establish that the deployed frontend, reverse proxy, API service, live SSE streams, voice provider, and blockchain nodes are correctly wired together in the live environment.

The user-provided R076 summary claims that the public frontend is served from OVH2, HTTP redirects to HTTPS, DNS answers from Google/Cloudflare/OVH point to `151.80.107.29`, OVH4/AWS3 return nginx 444 for `artcb.me`, both blockchain nodes are healthy, and OVH DNS credentials are held in Doppler. These claims are treated here as **reported, not independently verified**. The file at `rapports/R076_p0_verification_dns_https_blockchain_isolation_2026-10-17.md` was not found at that exact path on the connected repository's `main` branch. The latest accessible commit search returned R075, commit `cbf19b15ba3597b32238b29520a96c132f36793f`.

## 2. Expertise activated

- React and TypeScript frontend integration.
- FastAPI routing, API contracts, and service health.
- Reverse proxy configuration, HTTPS/TLS, DNS, and deployment topology.
- Server-Sent Events (SSE), streaming proxies, reconnection, and browser event handling.
- KYC data privacy and personal-data exposure in URLs and logs.
- Secret management, API security, CORS, and production hardening.
- Blockchain node health and separation of web traffic from peer traffic.
- End-to-end test design, release gates, and evidence-based certification.
- GitHub repository synchronization and report-only change control.

## 3. Repository evidence observed

### 3.1 Frontend

The following files were retrieved from the default branch:

- `frontend/src/App.tsx`
- `frontend/src/api/guardian.ts`
- `frontend/src/components/KycPanel.tsx`
- `frontend/vite.config.ts`
- `frontend/package.json`

The application imports `checkGuardianHealth`, `listGuardianScenarios`, and `runGuardianScenario` from the API client. The client uses `VITE_API_URL` if configured, otherwise it makes same-origin relative requests. The Vite development configuration proxies `/api` to `http://127.0.0.1:8000`.

**Implication:** the development proxy is not, by itself, a production proxy. The live web server must explicitly route the required `/api/*` requests to the intended backend service, or the frontend must use a deliberately configured API origin with correct TLS and CORS settings. A frontend HTML response can load successfully even when every subsequent API call fails.

The KYC component opens an EventSource URL with first name, last name, document ID, and date of birth in query parameters. This is a privacy risk because URLs can be copied into access logs, reverse-proxy logs, monitoring systems, browser diagnostics, and support captures.

### 3.2 Backend

The retrieved `guardian_api/app.py` declares FastAPI and includes at least:

- `GET /api/health`
- `GET /api/artcb/status`
- `POST /api/simulation/run`
- `POST /api/llm-attack/run`
- `POST /api/llm-attack/stream`

The file also documents an SSE event sequence for the live LLM-attack path and sends `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers for that stream. The frontend API client separately expects `GET /api/scenarios` and `POST /api/scenarios/{scenarioId}/run`; the KYC panel expects `GET /api/kyc/stream`.

The code excerpts retrieved in this review do not, on their own, prove that every frontend-consumed route is registered in the deployed build, exposed through the production reverse proxy, and returns the exact payloads expected by the frontend. This must be checked against the complete current route table and a live end-to-end test.

### 3.3 Simulation and certification flags

The retrieved `guardian_api/scenario_controller.py` explicitly sets:

- `CERTIFIED_100 = False`
- `UNIQUE_HUMAN_PROVEN = False`
- `DATA_SOURCE = "SIMULATED"`

**Implication:** at least this controller's scenario results are explicitly simulated. A successful demonstration of this path is evidence that the simulation works; it is not proof that a real human identity has been verified or that the entire product has production certification.

## 4. Process / problem / solution

### 4.1 Frontend-to-backend routing

**Process:** The browser loads the frontend, then calls API endpoints. Same-origin calls need the production web server or reverse proxy to forward `/api/*` to FastAPI. Cross-origin calls instead require a reachable API origin and a compatible CORS policy.

**Problem:** The Vite proxy only applies to the development server. If production nginx serves static files but does not proxy `/api/*`, the frontend can render while health checks, scenarios, and KYC requests fail or hit the wrong service. A wrong `VITE_API_URL` can cause the same failure.

**Solution:** Choose and document one production topology:
1. **Preferred when sharing one public hostname:** browser uses relative `/api/*` URLs and nginx routes `/api/*` to the correct backend listener.
2. **Alternative:** configure a dedicated HTTPS API origin, restrict CORS to the exact public frontend origins, and verify every endpoint against that origin.

Build the frontend using the intended production environment, inspect the built assets for unintended localhost/private addresses, and test the actual deployed requests in a browser network panel.

### 4.2 API contract compatibility

**Process:** The frontend calls named endpoints and parses JSON fields or typed SSE event payloads. Types in TypeScript help during development but do not validate runtime responses from the server.

**Problem:** An endpoint can return HTTP 200 while the JSON shape differs from what the UI expects. Renamed fields, missing scenario IDs, invalid enum values, or a different SSE event name can leave panels empty or falsely imply that a workflow completed.

**Solution:** Create a route contract table containing method, path, authentication requirements, request schema, response schema, and owner. Test every frontend-consumed route in the deployed environment. Validate JSON responses against runtime schemas and assert required SSE event names and payload fields. Correlate each demo run using its `session_id` and `run_id`.

### 4.3 SSE and live event delivery

**Process:** SSE keeps an HTTP response open and delivers named events as the backend emits them. The frontend registers listeners for those event names and updates React state. nginx and other intermediaries must not buffer or prematurely close the stream.

**Problem:** A normal HTTP health check does not prove that a long-lived stream works. Proxy buffering, short read timeouts, an absent keep-alive strategy, a wrong event name, an unhandled server exception, or reconnection behavior can break the live graph while the static UI remains visible.

**Solution:** Test each SSE endpoint through the public HTTPS hostname, not only directly against localhost. Confirm the initial event, ordered progress events, terminal `done` event, clean stream closure, error display, and repeat-run behavior. Configure buffering and timeouts intentionally. Confirm that the deployed proxy preserves `text/event-stream` and does not cache the stream.

### 4.4 KYC data privacy

**Process:** The KYC panel currently builds an EventSource URL containing first name, last name, document ID, and date of birth as query parameters.

**Problem:** URLs are routinely captured by infrastructure and diagnostic tooling. TLS encrypts the URL in transit but does not prevent the URL from appearing in server-side access logs or browser diagnostics. This is avoidable exposure of personal data.

**Solution:** Before real personal data is used, redesign the flow to submit the sensitive fields through a protected POST request, then return a short-lived, scoped stream/session token that contains no personal information. Apply authentication and authorization, rate limits, retention controls, and redaction of query strings in relevant logs. Use synthetic data for public demos and label it clearly. This report recommends the correction; it does not modify application code.

### 4.5 CORS and public API access

**Process:** FastAPI currently configures CORS with `allow_origins=["*"]`, methods GET/POST/OPTIONS, and credentials disabled.

**Problem:** A wildcard origin is broad. Although wildcard origins with credentials disabled are not equivalent to credentialed cross-origin access, this setting does not provide an origin allowlist and should not be mistaken for authentication or authorization.

**Solution:** If the frontend and API share a hostname, prefer same-origin routing and remove unnecessary cross-origin access. Otherwise, list only the exact trusted production origins. Independently enforce authorization for sensitive operations, input validation, request-size limits, rate limiting, and safe error responses. Do not expose secrets or personal data in error messages.

### 4.6 Blockchain and website isolation

**Process:** DNS determines how hostnames resolve; nginx virtual hosts and firewall/routing rules determine what each server accepts. Blockchain peer communication may require separate ports and hostnames.

**Problem:** A correct apex-domain DNS answer and nginx 444 response for a particular Host header do not prove that all web traffic is isolated, nor do they prove that peer connectivity remains healthy. IPv6 records, cached DNS, alternate hostnames, direct-IP requests, or proxy paths can change the path.

**Solution:** Verify authoritative and public A/AAAA/CNAME answers, certificate and host routing from an external network, and node health using the actual node health/peer/consensus signals. Preserve the intended `n4.artcb.me` and `n3.artcb.me` endpoints and the peer ports required by the network. Use time-bounded traffic telemetry before making an absolute “no traffic reaches these hosts” claim.

## 5. P0 acceptance checklist — required before declaring the stack fully operational

### P0-A — Public web entrypoint
- [ ] From an external network, verify DNS A, AAAA, and CNAME answers for `artcb.me` and `www.artcb.me` through authoritative nameservers and at least Google Public DNS and Cloudflare.
- [ ] Verify `http://artcb.me/` redirects to the intended HTTPS URL without a loop.
- [ ] Verify the certificate hostname, validity period, and trust chain for both public names.
- [ ] Verify the served frontend build/version and confirm no stale or unexpected deployment is being served.

### P0-B — Production frontend/API wiring
- [ ] Confirm the production reverse proxy forwards every required `/api/*` path to the intended FastAPI service and port.
- [ ] Confirm the deployed frontend has the intended API base URL and no accidental localhost/private-network URL.
- [ ] Test `GET /api/health` from the public frontend origin and verify the expected service identity.
- [ ] Test `GET /api/scenarios` and run each supported scenario through the frontend.
- [ ] Test the KYC stream endpoint and the LLM attack stream separately; do not treat one stream's success as proof that the other works.
- [ ] Confirm every UI state is driven by actual API responses and stream events, with explicit error, timeout, and offline states.

### P0-C — SSE and frontend behavior
- [ ] Verify named SSE events arrive in order through the public reverse proxy.
- [ ] Verify no proxy buffering, premature timeout, or caching interrupts the stream.
- [ ] Verify clean completion, error handling, repeated runs, and browser refresh behavior.
- [ ] Verify the live graph and decision display correspond to the same `session_id` and `run_id` returned by the backend.
- [ ] Verify no UI shows “success” or “certified” when the backend reports failure, simulated data, or incomplete verification.

### P0-D — KYC privacy and security
- [ ] Remove personal identity fields from stream URLs before handling real personal data.
- [ ] Confirm log redaction for request URLs and sensitive fields.
- [ ] Confirm the public KYC demo uses synthetic data and labels its simulated nature.
- [ ] Restrict CORS where cross-origin access is necessary.
- [ ] Verify authentication, authorization, rate limits, and safe error responses for any sensitive or state-changing endpoint.

### P0-E — Backend runtime and dependencies
- [ ] Confirm the running process, systemd unit, listener, and deployment commit match the intended service.
- [ ] Confirm the required runtime environment variables are present without printing secret values.
- [ ] Exercise the optional LLM and voice paths with credentials injected from the approved secret manager; verify clear fallback behavior when either provider is unavailable.
- [ ] Confirm provider/API failures do not prevent Guardian from emitting the security decision and integrity result.
- [ ] Run backend unit/API tests and frontend production build/lint in the intended deployment environment.

### P0-F — Blockchain and isolation
- [ ] Verify OVH4 and AWS3 node health from their actual node endpoints, including peer connectivity and the network's required consensus/replication signal.
- [ ] Verify the website Host header routes to OVH2 and is rejected by the other hosts as intended.
- [ ] Inspect A/AAAA records, alternate names, virtual hosts, and firewall rules.
- [ ] Verify website isolation without blocking required blockchain peer traffic.
- [ ] Preserve timestamped, sanitized evidence for all results.

## 6. Release gate and completion definition

The stack should be declared **fully operational for the intended demo** only after all P0 checks pass on the deployed public path and a single end-to-end run proves this sequence:

1. Browser loads the expected TERMINATOR frontend over valid HTTPS.
2. Frontend reaches the intended backend health and scenario endpoints.
3. User starts a scenario; backend returns a unique run/session identifier.
4. Guardian emits the expected decision and integrity evidence.
5. SSE events arrive through the production proxy and update the visible UI in the correct order.
6. The KYC/LLM/voice path being demonstrated completes or reports a clear, non-misleading failure.
7. The UI accurately reflects whether results are simulated or live and whether verification passed.
8. Blockchain node health and peer connectivity remain intact after the web-domain cutover.

A screenshot of the frontend, a 200/301 response, a successful DNS lookup, or a healthy node by itself is not an end-to-end acceptance test.

## 7. P1 after the P0 gate

- Add an automated smoke-test job against the public deployment after every release.
- Add correlation IDs across frontend requests, API logs, Guardian events, and SSE streams; sanitize personal data and secrets.
- Add monitoring for API latency, SSE disconnects, provider failures, and node peer/consensus health.
- Document rollback steps for the frontend, reverse proxy, DNS, and service release.
- Publish a sanitized evidence bundle containing timestamps, test origin, response codes, build/commit IDs, and pass/fail outcomes.

## 8. Final conclusion

The repository evidence supports the conclusion that the main frontend/backend building blocks exist. It does **not** establish that all deployed routes, streaming paths, provider integrations, security controls, and blockchain interactions currently work together in production. The highest-priority remaining task is a repeatable, externally executed end-to-end acceptance run with sanitized evidence, plus remediation of KYC personal data in query strings before any real personal data is used.

**Audit outcome: PARTIAL IMPLEMENTATION — P0 END-TO-END VERIFICATION REQUIRED.**
