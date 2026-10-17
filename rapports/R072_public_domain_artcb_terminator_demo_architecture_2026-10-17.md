# R072 — Public Domain Access and Cross-Cloud Blockchain / TERMINATOR Demo Architecture

**Date:** 2026-10-17  
**Repository:** `vgactech/ARTCB-TERMINATOR`  
**Scope:** Architecture review and deployment acceptance plan for public access to the TERMINATOR web interface while ARTCB blockchain nodes operate across OVH and AWS.  
**Change policy:** Documentation-only. This report does not modify application code, DNS, TLS, servers, cloud resources, secrets, logs, or the separate `vgactech/artcb` repository.

## 1. Executive conclusion

**Architecture feasibility: YES. Current live readiness: NOT VERIFIED.**

A blockchain network can run across OVH and AWS without depending on the apex domain `artcb.me`, provided node-to-node communication uses reachable IP addresses or stable node hostnames and the protocol configuration does not make that apex hostname a hard dependency. DNS is a naming and discovery layer; it is not inherently the consensus mechanism.

ARTCB-TERMINATOR can expose a public web interface for pitches and live demos under the same registered domain namespace. The safer default is a dedicated subdomain such as **`https://terminator.artcb.me`** (or `demo.artcb.me`) rather than repointing the apex `artcb.me`. Existing repository evidence in the separate ARTCB project describes the apex and node-specific hostnames as blockchain-related endpoints. Changing the apex without an inventory could disrupt existing API, health, or node-routing expectations.

This report makes an architecture recommendation only. It does not claim that the DNS record, certificate, reverse proxy, frontend, API connectivity, or live blockchain state has been tested. No infrastructure change was made.

## 2. Expertise activated

- Distributed systems and blockchain peer networking.
- DNS architecture and domain/subdomain routing.
- Cloud and network architecture across OVH and AWS.
- HTTPS/TLS termination and reverse-proxy configuration.
- Frontend/backend integration and browser security (CORS, cookies, WebSockets/SSE).
- Public demo reliability, health checks, observability, and rollback planning.
- Security boundaries for public web interfaces and privileged backend tools.
- GitHub change control and evidence-based release acceptance.

## 3. Process: what depends on the domain, and what does not

### 3.1 Blockchain node communication

Nodes need a reliable way to locate and reach peers. That may be implemented with fixed public IP addresses, DNS hostnames, a peer registry, or a combination. Consensus and ledger replication can continue without the apex website domain if peer identities and network addresses remain valid.

**Problem to rule out:** the application may still embed `artcb.me` in peer seeds, signed announcements, callback URLs, CORS allowlists, TLS validation, or service configuration. Repointing or removing the domain without checking those dependencies can break discovery or client connectivity even though DNS is not conceptually required by a blockchain.

**Solution:** inventory all configured peer endpoints and externally advertised URLs. Preserve stable per-node hostnames or IPs for peer traffic. Test node-to-node health and consensus independently from the public web frontend.

### 3.2 Public interface

The web interface is a separate delivery concern. A browser resolves a public hostname, establishes HTTPS, downloads the frontend, and calls only the backend endpoints that the UI requires. A reverse proxy or ingress can route web requests to the frontend and selected API paths.

**Problem to rule out:** a page can load while the demo remains unusable because API URLs are hard-coded to localhost, a private address, a development port, or a different origin; CORS, WebSocket/SSE, authentication, or TLS can also fail.

**Solution:** configure a public frontend origin, route API traffic deliberately, and run a browser-level end-to-end smoke test from a network outside the hosting environment.

## 4. Recommended target layout

Preferred starting layout, subject to an endpoint inventory:

- `https://terminator.artcb.me/` — public TERMINATOR presentation and live demo interface.
- `https://artcb.me/` — preserve the current apex behavior until its consumers and routes have been verified.
- Existing node hostnames (for example, `n2`, `n3`, and `n4` under the domain) — preserve their current role unless an explicit, tested migration is approved.
- Backend and node-management endpoints — not exposed indiscriminately to the public Internet; publish only the read-only or authenticated operations the demo requires.

The specific subdomain is a recommendation, not a claim that its DNS record already exists. If the user requires the apex `artcb.me` itself to show TERMINATOR, first inventory every current apex route and consumer, then design path-based routing or a controlled migration with rollback. Do not change the apex blindly.

## 5. Process / problem / solution matrix

| Area | Process (plain-language explanation) | Failure mode to check | Recommended correction |
|---|---|---|---|
| DNS | Maps the chosen hostname to the web entry point. | Missing, stale, or conflicting record. | Add/verify the dedicated subdomain record and check resolution from external resolvers. |
| TLS | Proves the website identity and encrypts browser traffic. | Missing/expired certificate, wrong hostname, redirect loop. | Issue a certificate for the exact hostname; verify HTTPS and HTTP-to-HTTPS redirect. |
| Reverse proxy | Sends browser requests to the correct frontend/API service. | Wrong upstream, port collision, default web page, 502/504. | Configure explicit host routing and health-checked upstreams; keep internal ports private. |
| Frontend configuration | Tells browser code which public API origin to call. | localhost/private API URLs or mixed content. | Use deployment-specific public URLs and HTTPS throughout. |
| CORS / cookies | Browser rules govern cross-origin API access and session handling. | Browser blocks API calls or session is lost. | Allow only the intended origins; set secure cookie and credential policy deliberately. |
| SSE / WebSocket | Carries live demo events or streaming updates to the browser. | Proxy buffering/timeouts or failed upgrade/stream. | Verify streaming through the production proxy and configure appropriate timeouts/buffering. |
| Blockchain peers | Nodes discover and contact one another independently of the presentation page. | Peer seeds or signed announcements depend on a changed hostname. | Preserve node endpoint identity; test peer health and consensus separately. |
| Demo safety | UI requests operations from backend services. | Public route exposes admin tools, secrets, or destructive calls. | Use least-privilege demo credentials, allowlisted operations, rate limits, and read-only defaults. |
| Availability | Monitoring detects failed frontend or backend paths. | Homepage returns 200 while API/demo is broken. | Add separate frontend, API, peer-health, and end-to-end demo checks. |

## 6. Acceptance checklist before calling the service pitch-ready

### P0 — public access
- [ ] The selected hostname resolves publicly to the intended entry point.
- [ ] HTTPS certificate is valid for the exact hostname and HTTP redirects to HTTPS.
- [ ] The interface loads from a clean browser on an external network.
- [ ] No frontend assets or API requests target localhost, private IPs, or development-only ports.
- [ ] The main demo path works end-to-end, not just the landing page.

### P0 — blockchain and backend separation
- [ ] OVH and AWS nodes can reach their configured peers without depending on the TERMINATOR frontend hostname.
- [ ] Node health and consensus/replication checks pass independently of the web UI.
- [ ] Public UI routes expose only the intended API methods; privileged management endpoints remain protected.
- [ ] A frontend or voice/demo feature failure cannot silently change or bypass a blockchain/security decision.

### P1 — live pitch resilience
- [ ] Live SSE/WebSocket events work through the public proxy where used.
- [ ] Monitoring distinguishes frontend, API, and node failures.
- [ ] A documented rollback can restore the previous apex/subdomain routing.
- [ ] A static presentation/fallback state is available if live backend dependencies fail, and is clearly labeled as simulated when applicable.

Record the timestamp, tested hostname, HTTP/TLS result, frontend build/version, backend health, peer status, and test result. Never place API keys, credentials, or raw secret-bearing logs in the report.

## 7. Important evidence limitation

The previous R071 audit classified the reported OVH2 Guardian, port 8002, Doppler, ElevenLabs, frontend, and redirect states as **not independently verified** because no live server/browser/provider checks were available. The current review likewise cannot certify DNS ownership/configuration, TLS status, the live frontend, or OVH/AWS node health from repository text alone.

Search results in the separate ARTCB repository contained historical references to `artcb.me` and per-node hostnames, and historical notes that some deployments had TLS or node synchronization gaps. Those are historical repository references, not a measurement of the current live state. This report does not modify or deploy anything in that separate repository.

## 8. Recommended implementation sequence

1. Inventory the current apex and all node hostnames, API consumers, TLS certificates, peer seeds, and browser API URLs.
2. Choose a dedicated TERMINATOR subdomain by default; do not overwrite the apex while its current responsibilities are unknown.
3. Configure DNS and HTTPS for the subdomain and route it to the existing TERMINATOR frontend service.
4. Configure the frontend's API origin and proxy only the necessary endpoints.
5. Run external-browser smoke tests plus independent OVH/AWS peer and blockchain health checks.
6. Capture evidence and create a follow-up report. Only then declare the pitch/demo endpoint ready.

## 9. Final assessment

**YES — feasible without making the apex domain a blockchain dependency.** The recommended design is to keep blockchain peer networking stable across OVH and AWS and publish TERMINATOR at a dedicated HTTPS subdomain under `artcb.me`. Preserve the apex until its current behavior is understood.

**Status:** Architecture recommendation ready; live deployment and public reachability not verified. No infrastructure or application files were changed by this report.
